"""
Handler: Bid Brief Drafting
Step 12 in Step Functions workflow
Generates executive bid brief for human review using Bedrock Claude
Input: Requirements, compliance, risks, evidence
Output: Structured bid brief
"""

import json
import logging
from typing import Any

from src.services.bedrock_service import BedrockService
from src.repositories.tender_repository import TenderRepository

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Generate bid brief summary for human decision-maker.
    
    Args:
        event: {"tender_id": "...", "company_id": "MAYZEROCK"}
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "recommendation": "GO|CONDITIONAL|NO_GO",
            "confidence": float,
            "brief_generated": true,
            "status": "SUCCESS"
        }
    """
    try:
        tender_id = event.get("tender_id")
        company_id = event.get("company_id", "MAYZEROCK")
        
        logger.info(f"Generating bid brief for {tender_id}")
        
        # Gather context
        repo = TenderRepository()
        tender = repo.get_tender_record(tender_id=tender_id)
        
        metadata = tender.get("metadata", {})
        requirements = tender.get("requirements", [])
        compliance_summary = tender.get("compliance_summary", {})
        risk_summary = tender.get("risk_summary", {})
        
        # Load prompt template
        with open("src/prompts/bid_drafting.txt") as f:
            prompt_template = f.read()
        
        # Build context
        prompt = prompt_template.replace(
            "{TENDER_METADATA}",
            json.dumps(metadata, indent=2)
        ).replace(
            "{REQUIREMENTS_SUMMARY}",
            json.dumps({
                "total": len(requirements),
                "categories": {}  # TODO: aggregate by category
            }, indent=2)
        ).replace(
            "{COMPLIANCE_STATUS}",
            json.dumps(compliance_summary, indent=2)
        ).replace(
            "{RISK_STATUS}",
            json.dumps(risk_summary, indent=2)
        ).replace(
            "{EVIDENCE_SUMMARY}",
            json.dumps({
                "chunks_retrieved": tender.get("total_evidence_chunks", 0)
            }, indent=2)
        )
        
        # Call Bedrock
        service = BedrockService()
        response = service.invoke_model_with_json(
            prompt=prompt,
            max_tokens=6000
        )
        
        # Parse brief
        brief = {}
        try:
            brief = json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse bid brief: {str(e)}")
            brief = {
                "executive_summary": "Unable to generate brief",
                "recommendation": "CONDITIONAL",
                "confidence": 0.0,
                "sections": [],
                "error": str(e)
            }
        
        # Store in DynamoDB
        repo.update_tender_record(
            tender_id=tender_id,
            updates={
                "bid_brief": brief,
                "bid_recommendation": brief.get("recommendation", "CONDITIONAL"),
                "bid_confidence": brief.get("confidence", 0.0)
            }
        )
        
        logger.info(f"Bid brief generated: recommendation={brief.get('recommendation')}")
        
        return {
            "tender_id": tender_id,
            "recommendation": brief.get("recommendation", "CONDITIONAL"),
            "confidence": brief.get("confidence", 0.0),
            "brief_generated": True,
            "status": "SUCCESS"
        }
    
    except Exception as e:
        logger.error(f"Error generating bid brief: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e)
        }
