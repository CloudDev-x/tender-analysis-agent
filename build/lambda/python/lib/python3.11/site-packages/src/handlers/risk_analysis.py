"""
Handler: Risk Analysis
Step 11 in Step Functions workflow
Uses Bedrock Claude to identify and assess risks
Input: Requirements, compliance status, company capabilities
Output: Risk assessments
"""

import json
import logging
from typing import Any

from src.config.aws_clients import get_s3_client
from src.services.bedrock_service import BedrockService
from src.repositories.tender_repository import TenderRepository

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Use Bedrock Claude to analyze risks in bid.
    
    Args:
        event: {"tender_id": "...", "company_id": "MAYZEROCK"}
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "risks_identified": int,
            "high_risk_count": int,
            "status": "SUCCESS"
        }
    """
    try:
        tender_id = event.get("tender_id")
        company_id = event.get("company_id", "MAYZEROCK")
        
        logger.info(f"Analyzing risks for {tender_id}")
        
        # Gather context
        repo = TenderRepository()
        tender = repo.get_tender_record(tender_id=tender_id)
        company = repo.get_company_record(company_id=company_id)
        
        requirements = tender.get("requirements", [])
        compliance_summary = tender.get("compliance_summary", {})
        evidence = tender.get("evidence", {})
        
        # Load prompt template
        with open("src/prompts/risk_analysis.txt") as f:
            prompt_template = f.read()
        
        # Build context
        prompt = prompt_template.replace(
            "{COMPANY_CAPABILITIES}",
            json.dumps(company.get("capabilities", []), indent=2)
        ).replace(
            "{EXTRACTED_REQUIREMENTS}",
            json.dumps(requirements[:10], indent=2)  # Limit to first 10 for context
        ).replace(
            "{COMPLIANCE_ASSESSMENTS}",
            json.dumps(compliance_summary, indent=2)
        )
        
        # Call Bedrock
        service = BedrockService()
        response = service.invoke_model_with_json(
            prompt=prompt,
            max_tokens=4000
        )
        
        # Parse risks
        risks = []
        try:
            risks_list = json.loads(response)
            risks = risks_list if isinstance(risks_list, list) else []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse risk analysis: {str(e)}")
        
        # Count by level
        high_count = sum(1 for r in risks if r.get("level") == "HIGH")
        medium_count = sum(1 for r in risks if r.get("level") == "MEDIUM")
        low_count = sum(1 for r in risks if r.get("level") == "LOW")
        
        # Store in DynamoDB
        repo.update_tender_record(
            tender_id=tender_id,
            updates={
                "risks": risks,
                "risk_summary": {
                    "total": len(risks),
                    "high": high_count,
                    "medium": medium_count,
                    "low": low_count
                }
            }
        )
        
        logger.info(f"Risk analysis complete: {high_count} HIGH, {medium_count} MEDIUM, {low_count} LOW")
        
        return {
            "tender_id": tender_id,
            "risks_identified": len(risks),
            "high_risk_count": high_count,
            "medium_risk_count": medium_count,
            "low_risk_count": low_count,
            "status": "SUCCESS"
        }
    
    except Exception as e:
        logger.error(f"Error in risk analysis: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e)
        }
