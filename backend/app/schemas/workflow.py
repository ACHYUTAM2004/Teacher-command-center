from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# --- 1. Sub-Schemas for Structured Educational Deliverables ---

class StandardMapping(BaseModel):
    code: str = Field(..., description="Official standard code, e.g., NGSS-MS-PS2-2")
    framework: str = Field(..., description="Curriculum framework, e.g., NGSS")
    description: str
    alignment_rationale: str

class TimelineBlock(BaseModel):
    phase_name: str = Field(..., description="e.g., Hook, Direct Instruction, Lab Activity, Wrap-Up")
    duration_minutes: int
    teacher_actions: str
    student_actions: str

class LessonPlanSchema(BaseModel):
    title: str
    grade: int
    subject: str
    total_duration_minutes: int
    learning_objectives: List[str]
    standards: List[StandardMapping]
    required_materials: List[str]
    safety_precautions: List[str]
    timeline: List[TimelineBlock]

class WorksheetQuestion(BaseModel):
    question_number: int
    prompt: str
    mapped_objective: str
    scaffold_hint: Optional[str] = Field(None, description="Populated for differentiated/IEP versions")
    sentence_starter: Optional[str] = Field(None, description="Populated for differentiated/IEP versions")

class WorksheetSchema(BaseModel):
    title: str
    is_differentiated: bool = False
    applied_accommodations: List[str] = Field(default_factory=list)
    instructions: str
    materials_checklist: List[str]
    data_table_headers: List[str] = Field(default_factory=list)
    questions: List[WorksheetQuestion]

class AssessmentItem(BaseModel):
    item_number: int
    question_type: str = Field(..., description="multiple_choice, short_answer, calculation")
    prompt: str
    options: Optional[List[str]] = None
    correct_answer: str
    points: int
    mapped_objective: str

class AssessmentSchema(BaseModel):
    title: str
    total_points: int
    items: List[AssessmentItem]

class RubricCriterion(BaseModel):
    criterion_name: str
    weight_points: int
    level_4_exemplary: str
    level_3_proficient: str
    level_2_developing: str
    level_1_beginning: str

class RubricSchema(BaseModel):
    title: str
    total_points: int
    criteria: List[RubricCriterion]

class QAReportSchema(BaseModel):
    deterministic_passed: bool
    standard_verified: bool
    duration_matches: bool
    rubric_points_valid: bool
    equipment_available: bool
    ai_critic_passed: bool
    grade_appropriate: bool
    scope_aligned: bool
    revision_notes: List[str] = Field(default_factory=list)

# --- 2. API Request & Response Contracts ---

class CreateWorkflowRequest(BaseModel):
    class_id: Optional[str] = Field(None, description="Linked classroom profile ID")
    grade: int = Field(..., ge=6, le=8, description="Target grade level (MVP: 6-8)")
    subject: str = Field("Science", description="Subject area (MVP: Science)")
    topic: str = Field(..., description="Specific topic, e.g., 'Newton's Second Law'")
    duration_minutes: int = Field(50, description="Total lesson duration in minutes")
    class_size: int = Field(28, description="Total number of students")
    activity_type: str = Field(..., description="e.g., 'Hands-on Lab'")
    learning_objective: Optional[str] = Field(None, description="Optional custom learning objective")
    available_equipment: List[str] = Field(default_factory=list, description="e.g., ['Dynamics Carts', 'Spring Scales', '200g Masses']")
    accommodations: List[str] = Field(default_factory=list, description="e.g., ['Formula triangles', 'Sentence starters']")
    deliverables: List[str] = Field(
        default=["lesson_plan", "worksheet", "differentiated_worksheet", "assessment", "rubric"],
        description="Requested output document types"
    )

class WorkflowResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: str
    current_step: str

class WorkflowPackageResponse(BaseModel):
    workflow_id: str
    status: str
    lesson_plan: Optional[LessonPlanSchema] = None
    worksheet: Optional[WorksheetSchema] = None
    differentiated_worksheet: Optional[WorksheetSchema] = None
    assessment: Optional[AssessmentSchema] = None
    rubric: Optional[RubricSchema] = None
    qa_report: Optional[QAReportSchema] = None