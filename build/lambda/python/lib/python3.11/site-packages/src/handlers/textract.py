"""
Handler: Textract Orchestration
Step 4-5 in Step Functions workflow
Starts Textract DetectDocumentText async job and polls for completion
Input: S3 key, tender_id
Output: Textract job ID and status
"""

import json
import logging
from typing import Any

from src.config.aws_clients import get_textract_client
from src.config.settings import TEXTRACT_CONFIDENCE_THRESHOLD
from src.services.textract_service import TextractService
from src.repositories.tender_repository import TenderRepository

logger = logging.getLogger(__name__)


def start_textract_job(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Start async Textract DetectDocumentText job.
    Step Functions will poll this job in subsequent states.
    
    Args:
        event: {"tender_id": "...", "s3_bucket": "...", "s3_key": "..."}
        context: Lambda context
    
    Returns:
        {"job_id": "...", "tender_id": "...", "status": "STARTED"}
    """
    try:
        tender_id = event.get("tender_id")
        s3_bucket = event.get("s3_bucket")
        s3_key = event.get("s3_key")
        
        logger.info(f"Starting Textract job for {tender_id}")
        
        service = TextractService()
        job_id = service.start_document_text_detection(
            s3_bucket=s3_bucket,
            s3_key=s3_key
        )
        
        logger.info(f"Textract job started: {job_id}")
        
        return {
            "tender_id": tender_id,
            "job_id": job_id,
            "status": "STARTED"
        }
    
    except Exception as e:
        logger.error(f"Error starting Textract job: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e)
        }


def get_textract_results(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Poll Textract job status and extract results when complete.
    
    Args:
        event: {"job_id": "...", "tender_id": "..."}
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "pages_detected": integer,
            "confidence": float,
            "text": "extracted text",
            "status": "COMPLETE|PENDING|FAILED"
        }
    """
    try:
        tender_id = event.get("tender_id")
        job_id = event.get("job_id")
        
        logger.info(f"Polling Textract job {job_id} for {tender_id}")
        
        service = TextractService()
        result = service.get_document_text_detection(job_id=job_id)
        
        if result["status"] == "SUCCEEDED":
            # Extract text from response
            text = result.get("text", "")
            confidence = result.get("confidence", 0.0)
            pages_detected = result.get("pages", 0)
            
            # Store extracted text in S3
            from src.config.aws_clients import get_s3_client
            s3 = get_s3_client()
            s3.put_object(
                Bucket=event.get("s3_bucket"),
                Key=f"processing/{tender_id}/textract/extracted.json",
                Body=json.dumps({
                    "text": text,
                    "confidence": confidence,
                    "pages": pages_detected
                }),
                ServerSideEncryption="aws:kms"
            )
            
            return {
                "tender_id": tender_id,
                "job_id": job_id,
                "status": "COMPLETE",
                "pages_detected": pages_detected,
                "confidence": confidence,
                "text_preview": text[:500]
            }
        
        elif result["status"] == "IN_PROGRESS":
            return {
                "tender_id": tender_id,
                "job_id": job_id,
                "status": "PENDING"
            }
        
        else:  # FAILED or PARTIAL
            return {
                "tender_id": tender_id,
                "job_id": job_id,
                "status": "FAILED",
                "error": result.get("error", "Unknown error")
            }
    
    except Exception as e:
        logger.error(f"Error getting Textract results: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e)
        }
