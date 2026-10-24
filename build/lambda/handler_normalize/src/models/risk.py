# =============================================================================
# Risk Model
# =============================================================================

from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAssessment(BaseModel):
    """Risk assessment for a requirement or tender."""
    risk_id: str
    requirement_id: Optional[str] = None
    level: RiskLevel
    category: str = Field(..., description="Category (deadline, scope, capacity, technical, financial, etc.)")
    description: str = Field(..., min_length=10)
    mitigation_recommendation: str = Field(..., min_length=10)
    detected_by: str = Field(..., description="RULE or BEDROCK")
    confidence: float = Field(..., ge=0.0, le=1.0)
    requires_escalation: bool = False
    assessed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = False


class RiskSummary(BaseModel):
    """Summary of all risks identified for a tender."""
    tender_id: str
    risks: list[RiskAssessment]
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    escalation_required: bool = False

    def update_counts(self) -> None:
        """Recalculate risk level counts."""
        self.critical_count = sum(1 for r in self.risks if r.level == RiskLevel.CRITICAL)
        self.high_count = sum(1 for r in self.risks if r.level == RiskLevel.HIGH)
        self.medium_count = sum(1 for r in self.risks if r.level == RiskLevel.MEDIUM)
        self.low_count = sum(1 for r in self.risks if r.level == RiskLevel.LOW)
        self.escalation_required = any(r.requires_escalation for r in self.risks)
