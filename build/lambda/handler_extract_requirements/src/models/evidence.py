# =============================================================================
# Evidence Model
# =============================================================================

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class EvidenceChunk(BaseModel):
    """Text chunk retrieved from Bedrock Knowledge Base."""
    chunk_id: str
    document_title: str
    document_type: str = Field(..., description="e.g., certification, project, policy")
    text_content: str = Field(..., min_length=10)
    s3_location: Optional[str] = None
    retrieval_score: float = Field(..., ge=0.0, le=1.0, description="KB similarity score")
    metadata: dict = Field(default_factory=dict)
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)


class EvidenceQuery(BaseModel):
    """Query sent to Knowledge Base."""
    requirement_id: str
    query_text: str
    max_results: int = 5
    score_threshold: float = 0.70


class EvidenceRetrievalResult(BaseModel):
    """Result of Knowledge Base retrieval."""
    query: EvidenceQuery
    chunks: list[EvidenceChunk]
    total_retrieved: int = 0
    queries_used: int = 1  # How many KB queries were made

    def filter_by_threshold(self, threshold: float) -> list[EvidenceChunk]:
        """Return chunks above score threshold."""
        return [c for c in self.chunks if c.retrieval_score >= threshold]
