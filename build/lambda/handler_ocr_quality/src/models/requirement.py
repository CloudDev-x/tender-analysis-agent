# =============================================================================
# Requirement Model
# =============================================================================

from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class RequirementCategory(str, Enum):
    """Requirement classification categories."""
    TECHNICAL = "TECHNICAL"
    COMMERCIAL = "COMMERCIAL"
    FINANCIAL = "FINANCIAL"
    LEGAL = "LEGAL"
    REGULATORY = "REGULATORY"
    COMPLIANCE = "COMPLIANCE"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    EXPERIENCE = "EXPERIENCE"
    PERSONNEL = "PERSONNEL"
    DOCUMENTATION = "DOCUMENTATION"
    DELIVERABLE = "DELIVERABLE"
    DEADLINE = "DEADLINE"
    EVALUATION = "EVALUATION"
    OTHER = "OTHER"


class RequirementSource(BaseModel):
    """Source location of the requirement in the tender document."""
    page: int | str = Field(..., description="Page number or 'unknown'")
    section: Optional[str] = Field(None, description="Section or clause reference")
    text: str = Field(..., description="Verbatim source text from tender")


class Requirement(BaseModel):
    """Extracted tender requirement."""
    requirement_id: str = Field(..., pattern=r"^REQ-[0-9]{3,}$")
    category: RequirementCategory
    description: str = Field(..., min_length=10)
    mandatory: bool = Field(..., description="Whether this requirement is mandatory")
    evidence_required: bool = Field(..., description="Whether evidence is needed to satisfy this requirement")
    deadline: Optional[datetime] = None
    source: RequirementSource
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence (0-1)")

    class Config:
        use_enum_values = False
