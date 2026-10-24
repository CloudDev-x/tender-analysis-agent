"""
Handler: Persistence
Step 14 in Step Functions workflow
Finalizes tender record and moves results to outputs folder
Input: Validated tender record
Output: Final output files in S3
"""

import json
import logging
from datetime import datetime
from typing import Any

from src.config.aws_clients import get_s3_client
from src.repositories.tender_repository import TenderRepository

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Persist final results to S3 outputs folder.
    
    Args:
        event: {"tender_id": "...", "s3_bucket": "..."}
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "output_location": "s3://bucket/outputs/...",
            "status": "SUCCESS"
        }
    """
    try:
        tender_id = event.get("tender_id")
        s3_bucket = event.get("s3_bucket")
        
        logger.info(f"Persisting results for {tender_id}")
        
        # Get tender record
        repo = TenderRepository()
        tender = repo.get_tender_record(tender_id=tender_id)
        
        # Prepare output document
        output_doc = {
            "tender_id": tender_id,
            "processed_at": datetime.utcnow().isoformat(),
            "metadata": tender.get("metadata", {}),
            "requirements": tender.get("requirements", []),
            "compliance_summary": tender.get("compliance_summary", {}),
            "risk_summary": tender.get("risk_summary", {}),
            "bid_brief": tender.get("bid_brief", {}),
            "bid_recommendation": tender.get("bid_recommendation", "CONDITIONAL"),
            "bid_confidence": tender.get("bid_confidence", 0.0)
        }
        
        # Write to S3
        s3 = get_s3_client()
        output_key = f"outputs/{tender_id}/bid_brief.json"
        
        s3.put_object(
            Bucket=s3_bucket,
            Key=output_key,
            Body=json.dumps(output_doc, indent=2),
            ServerSideEncryption="aws:kms",
            ContentType="application/json"
        )
        
        # Update tender record with finalization timestamp
        repo.update_tender_record(
            tender_id=tender_id,
            updates={
                "workflow_status": "COMPLETED",
                "output_location": f"s3://{s3_bucket}/{output_key}",
                "completed_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Results persisted to {output_key}")
        
        return {
            "tender_id": tender_id,
            "output_location": f"s3://{s3_bucket}/{output_key}",
            "status": "SUCCESS"
        }
    
    except Exception as e:
        logger.error(f"Error persisting results: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e)
        }
