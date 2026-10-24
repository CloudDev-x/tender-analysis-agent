# =============================================================================
# Lambda Handler: Intake
# Validates S3 upload and creates tender record
# =============================================================================

import json
import logging
from datetime import datetime
from typing import Any

from ..config import get_settings
from ..models.tender import TenderRecord, TenderStatus
from ..repositories import TenderRepository
from ..services import S3Service

logger = logging.getLogger(__name__)
settings = get_settings()


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler for intake validation.
    
    Event source: S3 event notification
    Event structure:
    {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "mayzerock-tender-tenders-prod"},
                    "object": {"key": "incoming/TND-001/original.pdf"}
                }
            }
        ]
    }
    """
    logger.info(f"Intake handler invoked with event: {json.dumps(event)}")

    try:
        # Parse S3 event
        records = event.get("Records", [])
        if not records:
            logger.warning("No S3 records in event")
            return {"statusCode": 400, "body": "No S3 records"}

        for record in records:
            s3_info = record.get("s3", {})
            bucket = s3_info.get("bucket", {}).get("name", "")
            key = s3_info.get("object", {}).get("key", "")

            if not bucket or not key:
                logger.warning(f"Invalid S3 event structure: bucket={bucket}, key={key}")
                continue

            # Validate bucket
            if bucket != settings.TENDER_BUCKET:
                logger.error(f"Upload to unexpected bucket: {bucket}")
                return {"statusCode": 403, "body": "Invalid bucket"}

            # Validate prefix
            if not key.startswith(settings.S3_INCOMING_PREFIX):
                logger.error(f"Upload to unexpected prefix: {key}")
                return {"statusCode": 403, "body": "Invalid prefix"}

            # Extract tender ID from key
            # Expected format: incoming/{tender_id}/original.pdf
            parts = key.split("/")
            if len(parts) < 2:
                logger.error(f"Invalid key format: {key}")
                return {"statusCode": 400, "body": "Invalid key format"}

            tender_id = parts[1]

            # Validate file
            s3_service = S3Service()
            metadata = s3_service.get_object_metadata(bucket, key)
            if metadata is None:
                logger.error(f"Failed to get metadata for {key}")
                return {"statusCode": 500, "body": "Failed to get file metadata"}

            file_size = metadata.get("size", 0)
            if file_size == 0:
                logger.error(f"Empty file uploaded: {key}")
                return {"statusCode": 400, "body": "Empty file"}

            if file_size > 10 * 1024 * 1024:  # 10 MB limit
                logger.error(f"File too large: {file_size} bytes")
                return {"statusCode": 413, "body": "File too large"}

            # Create tender record
            tender = TenderRecord(
                tender_id=tender_id,
                status=TenderStatus.INTAKE,
                uploaded_at=datetime.utcnow(),
                s3_original_key=key,
            )

            repo = TenderRepository()
            if not repo.put_tender(tender):
                logger.error(f"Failed to create tender record: {tender_id}")
                return {"statusCode": 500, "body": "Failed to create record"}

            logger.info(f"Created tender record: {tender_id} ({file_size} bytes)")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Intake validation complete"}),
        }

    except Exception as e:
        logger.error(f"Unexpected error in intake handler: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
