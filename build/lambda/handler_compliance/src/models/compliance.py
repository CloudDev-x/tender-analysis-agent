# =============================================================================
# Compliance Model
# =============================================================================

from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class ComplianceStatus(str, Enum):
    """Compliance status outcomes."""
    MET = "MET"
    PARTIAL = "PARTIAL"
    GAP = "GAP"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EvidenceSource(BaseModel):
    """Reference to evidence supporting compliance decision."""
    source_type: str = Field(..., description="DYNAMODB, KNOWLEDGE_BASE, or BOTH")
    dynamodb_pk: Optional[str] = None
    dynamodb_sk: Optional[str] = None
    kb_chunk_id: Optional[str] = None
    kb_score: Optional[float] = None
    s3_evidence_key: Optional[str] = None
    verified_at: Optional[datetime] = None


class ComplianceAssessment(BaseModel):
    """Compliance assessment for a single requirement."""
    requirement_id: str
    status: ComplianceStatus
    evidence: Optional[EvidenceSource] = None
    reason: str = Field(..., min_length=5)
    confidence: float = Field(..., ge=0.0, le=1.0)
    human_review_required: bool = False
    review_reason: Optional[str] = None
    assessed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = False


class ComplianceSummary(BaseModel):
    """Summary of all compliance assessments for a tender."""
    tender_id: str
    assessments: list[ComplianceAssessment]
    met_count: int = 0
    partial_count: int = 0
    gap_count: int = 0
    expired_count: int = 0
    unknown_count: int = 0
    not_applicable_count: int = 0

    def update_counts(self) -> None:
        """Recalculate status counts from assessments."""
        self.met_count = sum(1 for a in self.assessments if a.status == ComplianceStatus.MET)
        self.partial_count = sum(1 for a in self.assessments if a.status == ComplianceStatus.PARTIAL)
        self.gap_count = sum(1 for a in self.assessments if a.status == ComplianceStatus.GAP)
        self.expired_count = sum(1 for a in self.assessments if a.status == ComplianceStatus.EXPIRED)
        self.unknown_count = sum(1 for a in self.assessments if a.status == ComplianceStatus.UNKNOWN)
        self.not_applicable_count = sum(1 for a in self.assessments if a.status == ComplianceStatus.NOT_APPLICABLE)
