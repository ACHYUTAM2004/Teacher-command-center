import uuid
from typing import Optional
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import sentry_sdk

from app.models.base import SessionLocal
from app.schemas.workflow import (
    CreateWorkflowRequest,
    WorkflowResponse,
    WorkflowPackageResponse,
)
from app.services.knowledge_service import (
    load_okf_standards_from_disk,
    ingest_pdf_bytes,
    hybrid_retrieve,
)

sentry_sdk.init(dsn="", traces_sample_rate=1.0)

app = FastAPI(
    title="Teacher Command Center API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/v1/workflows", response_model=WorkflowResponse, tags=["Workflows"])
async def create_workflow(request: CreateWorkflowRequest):
    return WorkflowResponse(
        workflow_id=f"wf_{uuid.uuid4().hex[:8]}",
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        status="queued",
        current_step="classroom_context_loaded",
    )


@app.get("/api/v1/workflows/{workflow_id}", response_model=WorkflowPackageResponse, tags=["Workflows"])
async def get_workflow_package(workflow_id: str):
    return WorkflowPackageResponse(
        workflow_id=workflow_id,
        status="review",
    )


@app.get("/api/v1/knowledge/standards", tags=["Knowledge"])
async def list_okf_standards(
    grade: Optional[int] = None,
    subject: Optional[str] = None,
    topic: Optional[str] = None,
):
    return {"standards": load_okf_standards_from_disk(grade=grade, subject=subject, topic_query=topic)}


@app.post("/api/v1/resources/ingest", tags=["Knowledge"])
async def upload_and_ingest_pdf(
    grade: int = Form(..., ge=1, le=12),
    subject: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    file_bytes = await file.read()
    return ingest_pdf_bytes(db=db, file_bytes=file_bytes, filename=file.filename, grade=grade, subject=subject)


@app.get("/api/v1/knowledge/retrieve", tags=["Knowledge"])
async def test_hybrid_retrieval(
    query: str,
    grade: int = 10,
    subject: str = "Science",
    top_k: int = 5,
    db: Session = Depends(get_db),
):
    return hybrid_retrieve(db=db, query=query, grade=grade, subject=subject, top_k=top_k)