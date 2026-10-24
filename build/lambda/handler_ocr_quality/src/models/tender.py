# =============================================================================
# Tender Model
# =============================================================================

from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class TenderStatus(str, Enum):
    """Tender processing status."""
    INTAKE = "INTAKE"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    FAILED = "FAILED"


class TenderMetadata(BaseModel):
    """Extracted tender metadata."""
    tender_title: str
    issuing_organization: str
    project_scope: str
    submission_deadline: datetime
    project_location: Optional[str] = None
    contract_duration: Optional[str] = None
    estimated_value: Optional[float] = None
    evaluation_criteria: list[str] = Field(default_factory=list)
    contact_information: Optional[str] = None
    required_submission_method: Optional[str] = None


class TenderRecord(BaseModel):
    """Complete tender processing record."""
    tender_id: str
    status: TenderStatus
    uploaded_at: datetime
    metadata: Optional[TenderMetadata] = None
    s3_original_key: str = Field(..., description="S3 path to original PDF")
    s3_normalized_key: Optional[str] = None
    s3_textract_key: Optional[str] = None
    textract_job_id: Optional[str] = None
    requirement_count: int = 0
    compliance_summary: Optional[dict] = None
    human_review_required: bool = False
    review_reasons: list[str] = Field(default_factory=list)
    workflow_execution_id: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = False
