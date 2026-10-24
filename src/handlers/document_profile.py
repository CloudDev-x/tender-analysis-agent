"""
Handler: Document Profile
Step 2 in Step Functions workflow
Determines document type, page count, OCR quality flags
Input: S3 object metadata from intake
Output: DocumentProfile record in DynamoDB
"""

import json
import logging
from typing import Any

from src.config.aws_clients import get_s3_client, get_dynamodb_client
from src.models.tender import TenderRecord, TenderStatus
from src.repositories.tender_repository import TenderRepository

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Analyze uploaded PDF to determine:
    - Page count
    - File size
    - Scanned vs native text
    - Language detection (future)
    - OCR confidence gate recommendation
    
    Args:
        event: Step Functions input with tender_id, s3_bucket, s3_key
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "page_count": integer,
            "file_size_bytes": integer,
            "is_scanned": boolean,
            "ocr_confidence_gate": "PASS|REVIEW|FAIL",
            "notes": "..."
        }
    """
    try:
        tender_id = event.get("tender_id")
        s3_bucket = event.get("s3_bucket")
        s3_key = event.get("s3_key")
        
        logger.info(f"Profiling document: {tender_id} at s3://{s3_bucket}/{s3_key}")
        
        # Get object metadata from S3
        s3 = get_s3_client()
        response = s3.head_object(Bucket=s3_bucket, Key=s3_key)
        
        file_size_bytes = response.get("ContentLength", 0)
        
        # TODO: Use pdfplumber or pypdf to inspect PDF
        # For now, simple heuristics
        page_count = 1  # placeholder
        is_scanned = False  # placeholder
        
        # Decision logic for OCR gate
        if file_size_bytes > 50 * 1024 * 1024:  # >50MB
            ocr_gate = "FAIL"
            notes = "File too large for Textract"
        elif page_count > 500:
            ocr_gate = "REVIEW"
            notes = "Large document; manual review recommended"
        elif is_scanned:
            ocr_gate = "REVIEW"
            notes = "Scanned PDF; OCR quality may vary"
        else:
            ocr_gate = "PASS"
            notes = "Native PDF, should OCR cleanly"
        
        # Update tender record
        repo = TenderRepository()
        repo.update_tender_record(
            tender_id=tender_id,
            updates={
                "document_profile": {
                    "page_count": page_count,
                    "file_size_bytes": file_size_bytes,
                    "is_scanned": is_scanned,
                    "ocr_confidence_gate": ocr_gate,
                    "notes": notes,
                }
            }
        )
        
        return {
            "tender_id": tender_id,
            "page_count": page_count,
            "file_size_bytes": file_size_bytes,
            "is_scanned": is_scanned,
            "ocr_confidence_gate": ocr_gate,
            "notes": notes,
            "status": "SUCCESS"
        }
    
    except Exception as e:
        logger.error(f"Error profiling document: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e)
        }
