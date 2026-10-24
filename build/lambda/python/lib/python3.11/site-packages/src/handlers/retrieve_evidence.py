"""
Handler: Retrieve Evidence
Step 9 in Step Functions workflow
Queries Bedrock Knowledge Base for Mayzerock capabilities/evidence matching requirements
Input: Extracted requirements
Output: Evidence chunks stored in DynamoDB
"""

import json
import logging
from typing import Any

from src.config.aws_clients import get_dynamodb_client
from src.services.bedrock_kb_service import BedrockKBService
from src.repositories.tender_repository import TenderRepository
from src.models.evidence import EvidenceQuery, EvidenceRetrievalResult

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    For each requirement, query Knowledge Base for matching evidence.
    Store evidence chunks in DynamoDB for later compliance assessment.
    
    Args:
        event: {
            "tender_id": "...",
            "kb_id": "knowledge_base_id"
        }
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "evidence_queries": int,
            "evidence_chunks_retrieved": int,
            "status": "SUCCESS"
        }
    """
    try:
        tender_id = event.get("tender_id")
        kb_id = event.get("kb_id")
        
        logger.info(f"Retrieving evidence for {tender_id}")
        
        # Get requirements from DynamoDB
        repo = TenderRepository()
        tender = repo.get_tender_record(tender_id=tender_id)
        requirements = tender.get("requirements", [])
        
        # Query KB for each requirement
        kb_service = BedrockKBService()
        all_evidence = {}
        
        for i, req in enumerate(requirements):
            query_text = req.get("description", "")
            if not query_text:
                continue
            
            try:
                result = kb_service.retrieve_for_requirement(
                    query=query_text,
                    kb_id=kb_id,
                    max_results=3
                )
                
                all_evidence[f"REQ-{i}"] = {
                    "requirement": query_text,
                    "evidence_chunks": [
                        {
                            "content": chunk.get("content", ""),
                            "score": chunk.get("score", 0.0),
                            "metadata": chunk.get("metadata", {})
                        }
                        for chunk in result.get("chunks", [])
                    ]
                }
            
            except Exception as e:
                logger.warning(f"Failed to retrieve evidence for REQ-{i}: {str(e)}")
                all_evidence[f"REQ-{i}"] = {
                    "requirement": query_text,
                    "evidence_chunks": [],
                    "error": str(e)
                }
        
        # Store evidence in DynamoDB
        repo.update_tender_record(
            tender_id=tender_id,
            updates={
                "evidence": all_evidence,
                "evidence_queries_executed": len(requirements),
                "total_evidence_chunks": sum(
                    len(ev.get("evidence_chunks", []))
                    for ev in all_evidence.values()
                )
            }
        )
        
        chunks_retrieved = sum(
            len(ev.get("evidence_chunks", []))
            for ev in all_evidence.values()
        )
        
        logger.info(f"Retrieved {chunks_retrieved} evidence chunks for {len(requirements)} requirements")
        
        return {
            "tender_id": tender_id,
            "evidence_queries": len(requirements),
            "evidence_chunks_retrieved": chunks_retrieved,
            "status": "SUCCESS"
        }
    
    except Exception as e:
        logger.error(f"Error retrieving evidence: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e)
        }
