"""
Handler: OCR Quality Gate
Step 6 in Step Functions workflow
Validates Textract confidence and text quality; gates to manual review if needed
Input: Textract results
Output: Quality assessment; PASS/FAIL/REVIEW decision
"""

import json
import logging
from typing import Any

from src.config.settings import OCR_CONFIDENCE_THRESHOLD
from src.config.aws_clients import get_s3_client

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Gate OCR quality:
    - If confidence >= threshold → PASS (continue to normalization)
    - If confidence 0.70-0.85 → REVIEW (flag for human)
    - If confidence < 0.70 → FAIL (halt workflow, notify)
    
    Args:
        event: {
            "tender_id": "...",
            "job_id": "...",
            "confidence": 0.0-1.0,
            "pages_detected": int,
            "s3_bucket": "...",
            "s3_key": "..."
        }
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "gate_result": "PASS|REVIEW|FAIL",
            "confidence": float,
            "reason": "..."
        }
    """
    try:
        tender_id = event.get("tender_id")
        confidence = event.get("confidence", 0.0)
        pages_detected = event.get("pages_detected", 0)
        
        logger.info(f"OCR quality gate: {tender_id}, confidence={confidence}")
        
        # Gate logic
        if confidence >= OCR_CONFIDENCE_THRESHOLD:
            gate_result = "PASS"
            reason = f"OCR confidence {confidence:.2%} meets threshold {OCR_CONFIDENCE_THRESHOLD:.2%}"
        
        elif 0.70 <= confidence < OCR_CONFIDENCE_THRESHOLD:
            gate_result = "REVIEW"
            reason = f"OCR confidence {confidence:.2%} requires manual review"
        
        else:
            gate_result = "FAIL"
            reason = f"OCR confidence {confidence:.2%} below minimum 0.70; unrecoverable"
        
        # Additional flags
        if pages_detected > 100:
            reason += f"; {pages_detected} pages detected, may be resource-intensive"
        
        return {
            "tender_id": tender_id,
            "gate_result": gate_result,
            "confidence": confidence,
            "pages_detected": pages_detected,
            "reason": reason,
            "status": "SUCCESS"
        }
    
    except Exception as e:
        logger.error(f"Error in OCR quality gate: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e),
            "gate_result": "FAIL"
        }
