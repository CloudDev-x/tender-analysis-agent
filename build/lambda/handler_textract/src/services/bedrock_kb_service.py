# =============================================================================
# Bedrock Knowledge Base Service
# =============================================================================

import logging
from typing import Optional

from botocore.exceptions import ClientError

from ..config import get_bedrock_agent_client, get_settings
from ..models.evidence import EvidenceChunk, EvidenceQuery, EvidenceRetrievalResult

logger = logging.getLogger(__name__)


class BedrockKBService:
    """Bedrock Knowledge Base retrieval (S3 Vectors backend)."""

    def __init__(self) -> None:
        self.client = get_bedrock_agent_client()
        self.settings = get_settings()

    def retrieve_evidence(
        self,
        query: str,
        max_results: int = 5,
        score_threshold: float = 0.70,
    ) -> list[EvidenceChunk]:
        """
        Query Knowledge Base for relevant evidence.
        Returns list of EvidenceChunk objects.
        """
        if not self.settings.BEDROCK_KB_ID:
            logger.warning("BEDROCK_KB_ID not configured; skipping KB retrieval")
            return []

        try:
            response = self.client.retrieve(
                knowledgeBaseId=self.settings.BEDROCK_KB_ID,
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": max_results,
                    }
                },
                retrievalQuery={"text": query},
            )

            chunks = []
            for result in response.get("retrievalResults", []):
                score = result.get("score", 0.0)
                
                # Filter by threshold
                if score < score_threshold:
                    logger.debug(f"Skipping result with score {score:.2f} < {score_threshold}")
                    continue

                chunk = EvidenceChunk(
                    chunk_id=result.get("metadata", {}).get("id", "unknown"),
                    document_title=result.get("metadata", {}).get("title", "Unknown"),
                    document_type=result.get("metadata", {}).get("type", "unknown"),
                    text_content=result.get("content", {}).get("text", ""),
                    s3_location=result.get("location", {}).get("s3Location", {}).get("uri"),
                    retrieval_score=score,
                    metadata=result.get("metadata", {}),
                )
                chunks.append(chunk)

            logger.info(f"KB retrieval returned {len(chunks)} chunks for query: {query[:50]}...")
            return chunks

        except ClientError as e:
            logger.error(f"Knowledge Base retrieval failed: {e}")
            return []
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse KB response: {e}")
            return []

    def retrieve_for_requirement(
        self,
        requirement_id: str,
        requirement_text: str,
        max_results: int = 5,
    ) -> EvidenceRetrievalResult:
        """
        Retrieve evidence for a specific requirement.
        Returns EvidenceRetrievalResult with chunks and metadata.
        """
        query = EvidenceQuery(
            requirement_id=requirement_id,
            query_text=requirement_text,
            max_results=max_results,
            score_threshold=self.settings.RETRIEVAL_SCORE_THRESHOLD,
        )

        chunks = self.retrieve_evidence(
            query=requirement_text,
            max_results=max_results,
            score_threshold=query.score_threshold,
        )

        result = EvidenceRetrievalResult(
            query=query,
            chunks=chunks,
            total_retrieved=len(chunks),
        )

        return result
