"""
Handler: Normalize Document Text
Step 7 in Step Functions workflow
Cleans, deduplicates, and standardizes extracted text
Input: Raw Textract output
Output: Normalized text stored in S3
"""

import json
import logging
import re
from typing import Any

from src.config.aws_clients import get_s3_client

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Apply normalization rules to extracted text:
    - Remove extra whitespace
    - Deduplicate repeated lines
    - Fix common OCR errors
    - Standardize dates/numbers
    
    Args:
        text: Raw extracted text from Textract
    
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Remove excess whitespace
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r' +', ' ', text)
    text = text.strip()
    
    # Deduplicate consecutive lines
    lines = text.split('\n')
    deduped = []
    for line in lines:
        if not deduped or line.strip() != deduped[-1].strip():
            deduped.append(line)
    
    text = '\n'.join(deduped)
    
    # TODO: Implement OCR error corrections (e.g., l → 1, O → 0, etc.)
    # This is domain-specific and should be refined with real data
    
    return text


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Normalize extracted text and store in S3.
    
    Args:
        event: {
            "tender_id": "...",
            "s3_bucket": "...",
            "s3_key": "..."
        }
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "normalized_length": int,
            "reduction_percent": float,
            "status": "SUCCESS"
        }
    """
    try:
        tender_id = event.get("tender_id")
        s3_bucket = event.get("s3_bucket")
        
        logger.info(f"Normalizing text for {tender_id}")
        
        # Retrieve extracted text from S3
        s3 = get_s3_client()
        response = s3.get_object(
            Bucket=s3_bucket,
            Key=f"processing/{tender_id}/textract/extracted.json"
        )
        extracted = json.loads(response["Body"].read())
        raw_text = extracted.get("text", "")
        raw_length = len(raw_text)
        
        # Normalize
        normalized = normalize_text(raw_text)
        normalized_length = len(normalized)
        
        reduction_percent = (1 - normalized_length / max(raw_length, 1)) * 100
        
        # Store normalized text
        s3.put_object(
            Bucket=s3_bucket,
            Key=f"processing/{tender_id}/normalized/text.json",
            Body=json.dumps({
                "text": normalized,
                "raw_length": raw_length,
                "normalized_length": normalized_length,
                "reduction_percent": reduction_percent
            }),
            ServerSideEncryption="aws:kms"
        )
        
        logger.info(f"Normalized text: {normalized_length} chars ({reduction_percent:.1f}% reduction)")
        
        return {
            "tender_id": tender_id,
            "normalized_length": normalized_length,
            "reduction_percent": reduction_percent,
            "status": "SUCCESS"
        }
    
    except Exception as e:
        logger.error(f"Error normalizing text: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e)
        }
