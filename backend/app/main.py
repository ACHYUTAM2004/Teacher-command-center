import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk

from app.schemas.workflow import (
    CreateWorkflowRequest,
    WorkflowResponse,
    WorkflowPackageResponse,
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