import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.models.base import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    subjects = Column(JSON, default=list)
    grades = Column(JSON, default=list)
    teaching_style = Column(String, nullable=True)
    grading_preferences = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    classes = relationship("ClassRoom", back_populates="teacher")
    workflows = relationship("Workflow", back_populates="teacher")

class ClassRoom(Base):
    __tablename__ = "classes"

    id = Column(String, primary_key=True, default=generate_uuid)
    teacher_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    grade = Column(Integer, nullable=False)
    subject = Column(String, nullable=False)
    student_count = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, default=50)
    accommodations = Column(JSON, default=dict)
    available_equipment = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    teacher = relationship("User", back_populates="classes")
    workflows = relationship("Workflow", back_populates="classroom")

class Standard(Base):
    __tablename__ = "standards"

    id = Column(String, primary_key=True)  # e.g., "NGSS-MS-PS2-2"
    code = Column(String, unique=True, index=True, nullable=False)
    framework = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    grade_band = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    prerequisites = Column(JSON, default=list)
    assessed_skills = Column(JSON, default=list)
    forbidden_topics = Column(JSON, default=list)

class Resource(Base):
    __tablename__ = "resources"

    id = Column(String, primary_key=True, default=generate_uuid)
    teacher_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)  # e.g., textbook, pdf, lab_inventory
    s3_key = Column(String, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True, default=generate_uuid)
    teacher_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_id = Column(String, ForeignKey("classes.id", ondelete="SET NULL"), nullable=True)
    topic = Column(String, nullable=False)
    grade = Column(Integer, nullable=False)
    subject = Column(String, nullable=False)
    duration_minutes = Column(Integer, default=50)
    activity_type = Column(String, nullable=False)
    learning_objective = Column(Text, nullable=True)
    available_equipment = Column(JSON, default=list)
    accommodations = Column(JSON, default=dict)
    requested_deliverables = Column(JSON, default=list)
    status = Column(String, default="draft")  # draft, queued, running, review, approved, failed
    created_at = Column(DateTime(timezone=True), default=utcnow)

    teacher = relationship("User", back_populates="workflows")
    classroom = relationship("ClassRoom", back_populates="workflows")
    runs = relationship("WorkflowRun", back_populates="workflow", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="workflow", cascade="all, delete-orphan")

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="queued")  # queued, running, completed, failed
    current_step = Column(String, nullable=True)
    state_snapshot = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    workflow = relationship("Workflow", back_populates="runs")
    qa_reports = relationship("QAReport", back_populates="workflow_run", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(String, nullable=False)  # lesson_plan, worksheet, differentiated_worksheet, assessment, rubric
    title = Column(String, nullable=False)
    current_version = Column(Integer, default=1)
    status = Column(String, default="draft")  # draft, reviewed, approved
    pdf_s3_key = Column(String, nullable=True)
    docx_s3_key = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    workflow = relationship("Workflow", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    source = Column(String, nullable=False)  # ai_generated, teacher_edited, ai_updated, approved
    content_schema = Column(JSON, nullable=False)  # Structured Pydantic object stored as JSON
    created_at = Column(DateTime(timezone=True), default=utcnow)

    document = relationship("Document", back_populates="versions")

class QAReport(Base):
    __tablename__ = "qa_reports"

    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_run_id = Column(String, ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    deterministic_passed = Column(Boolean, default=False)
    deterministic_checks = Column(JSON, default=dict)
    ai_critic_passed = Column(Boolean, default=False)
    ai_critic_feedback = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    workflow_run = relationship("WorkflowRun", back_populates="qa_reports")

class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    source_entity = Column(String, nullable=False)  # e.g., "available_equipment" or "lesson_plan"
    target_document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    shared_reference_key = Column(String, nullable=False)  # e.g., "lab_masses"

class ResourceChunk(Base):
    __tablename__ = "resource_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    resource_id: Mapped[str] = mapped_column(ForeignKey("resources.id", ondelete="CASCADE"), index=True)
    grade: Mapped[int] = mapped_column(Integer, index=True)
    subject: Mapped[str] = mapped_column(String, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))