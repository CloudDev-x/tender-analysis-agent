"""
Handler: Output Validation
Step 13 in Step Functions workflow
Validates all bid outputs before persistence
Input: Tender record with all assessments
Output: Validation status
"""

import logging
from typing import Any

from src.repositories.tender_repository import TenderRepository

logger = logging.getLogger(__name__)


def validate_output(tender: dict) -> tuple[bool, list[str]]:
    """
    Validate tender record completeness.
    
    Returns: (is_valid, errors)
    """
    errors = []
    
    # Check required fields
    if not tender.get("metadata"):
        errors.append("Missing tender metadata")
    
    if not tender.get("requirements"):
        errors.append("No requirements extracted")
    
    if not tender.get("compliance_summary"):
        errors.append("Missing compliance assessment")
    
    if not tender.get("bid_brief"):
        errors.append("Missing bid brief")
    
    if not tender.get("bid_recommendation"):
        errors.append("Missing bid recommendation")
    
    # Check data quality
    compliance_summary = tender.get("compliance_summary", {})
    if compliance_summary.get("total_requirements", 0) == 0:
        errors.append("No requirements recorded in compliance summary")
    
    bid_confidence = tender.get("bid_confidence", 0.0)
    if bid_confidence < 0.0 or bid_confidence > 1.0:
        errors.append(f"Invalid bid confidence: {bid_confidence}")
    
    return len(errors) == 0, errors


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Validate tender record before persistence.
    
    Args:
        event: {"tender_id": "..."}
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "validation_passed": bool,
            "errors": [],
            "status": "SUCCESS"
        }
    """
    try:
        tender_id = event.get("tender_id")
        
        logger.info(f"Validating output for {tender_id}")
        
        # Get tender record
        repo = TenderRepository()
        tender = repo.get_tender_record(tender_id=tender_id)
        
        # Validate
        is_valid, errors = validate_output(tender)
        
        if is_valid:
            logger.info(f"Output validation passed for {tender_id}")
        else:
            logger.warning(f"Output validation failed for {tender_id}: {errors}")
        
        return {
            "tender_id": tender_id,
            "validation_passed": is_valid,
            "errors": errors,
            "status": "SUCCESS"
        }
    
    except Exception as e:
        logger.error(f"Error validating output: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "validation_passed": False,
            "errors": [str(e)],
            "status": "FAILED"
        }
