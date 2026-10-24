# =============================================================================
# Tender Repository
# =============================================================================

import json
import logging
from datetime import datetime
from typing import Optional

from botocore.exceptions import ClientError

from ..config import get_dynamodb_client, get_settings
from ..models.tender import TenderRecord, TenderStatus

logger = logging.getLogger(__name__)


class TenderRepository:
    """DynamoDB queries for tender records."""

    def __init__(self) -> None:
        self.client = get_dynamodb_client()
        self.settings = get_settings()
        self.table_name = self.settings.DYNAMODB_TABLE

    def put_tender(self, tender: TenderRecord) -> bool:
        """Create or update a tender record."""
        try:
            item = {
                "PK": {"S": f"TENDER#{tender.tender_id}"},
                "SK": {"S": "METADATA"},
                "status": {"S": tender.status.value},
                "uploaded_at": {"S": tender.uploaded_at.isoformat()},
                "updated_at": {"S": tender.updated_at.isoformat()},
                "s3_original_key": {"S": tender.s3_original_key},
            }

            if tender.metadata:
                item["metadata"] = {"S": json.dumps(tender.metadata.dict(), default=str)}
            if tender.s3_normalized_key:
                item["s3_normalized_key"] = {"S": tender.s3_normalized_key}
            if tender.s3_textract_key:
                item["s3_textract_key"] = {"S": tender.s3_textract_key}
            if tender.textract_job_id:
                item["textract_job_id"] = {"S": tender.textract_job_id}
            if tender.workflow_execution_id:
                item["workflow_execution_id"] = {"S": tender.workflow_execution_id}

            item["requirement_count"] = {"N": str(tender.requirement_count)}
            item["human_review_required"] = {"BOOL": tender.human_review_required}

            if tender.review_reasons:
                item["review_reasons"] = {"SS": tender.review_reasons}
            if tender.compliance_summary:
                item["compliance_summary"] = {"S": json.dumps(tender.compliance_summary, default=str)}

            # GSI1 for status index
            item["GSI1PK"] = {"S": f"STATUS#{tender.status.value}"}
            item["GSI1SK"] = {"S": tender.uploaded_at.isoformat()}

            self.client.put_item(TableName=self.table_name, Item=item)
            logger.info(f"Created/updated tender {tender.tender_id}")
            return True

        except ClientError as e:
            logger.error(f"Failed to put tender {tender.tender_id}: {e}")
            return False

    def get_tender(self, tender_id: str) -> Optional[TenderRecord]:
        """Retrieve a tender record."""
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={
                    "PK": {"S": f"TENDER#{tender_id}"},
                    "SK": {"S": "METADATA"},
                },
            )

            if "Item" not in response:
                logger.warning(f"Tender {tender_id} not found")
                return None

            item = response["Item"]
            tender = TenderRecord(
                tender_id=tender_id,
                status=TenderStatus(item["status"]["S"]),
                uploaded_at=datetime.fromisoformat(item["uploaded_at"]["S"]),
                s3_original_key=item["s3_original_key"]["S"],
                s3_normalized_key=item.get("s3_normalized_key", {}).get("S"),
                s3_textract_key=item.get("s3_textract_key", {}).get("S"),
                textract_job_id=item.get("textract_job_id", {}).get("S"),
                workflow_execution_id=item.get("workflow_execution_id", {}).get("S"),
                requirement_count=int(item.get("requirement_count", {}).get("N", 0)),
                human_review_required=item.get("human_review_required", {}).get("BOOL", False),
                review_reasons=item.get("review_reasons", {}).get("SS", []),
                updated_at=datetime.fromisoformat(item.get("updated_at", {}).get("S", "")),
            )

            if "metadata" in item:
                tender.metadata = json.loads(item["metadata"]["S"])
            if "compliance_summary" in item:
                tender.compliance_summary = json.loads(item["compliance_summary"]["S"])

            logger.info(f"Retrieved tender {tender_id}")
            return tender

        except ClientError as e:
            logger.error(f"Failed to get tender {tender_id}: {e}")
            return None

    def list_tenders_by_status(self, status: TenderStatus, limit: int = 20) -> list[TenderRecord]:
        """List tenders by status using GSI1."""
        try:
            response = self.client.query(
                TableName=self.table_name,
                IndexName="GSI1-StatusIndex",
                KeyConditionExpression="GSI1PK = :pk",
                ExpressionAttributeValues={":pk": {"S": f"STATUS#{status.value}"}},
                Limit=limit,
            )

            tenders = []
            for item in response.get("Items", []):
                tender_id = item["PK"]["S"].replace("TENDER#", "")
                tender = self.get_tender(tender_id)
                if tender:
                    tenders.append(tender)

            logger.info(f"Listed {len(tenders)} tenders with status {status.value}")
            return tenders

        except ClientError as e:
            logger.error(f"Failed to list tenders by status {status.value}: {e}")
            return []

    def update_tender_status(self, tender_id: str, status: TenderStatus) -> bool:
        """Update tender processing status."""
        try:
            self.client.update_item(
                TableName=self.table_name,
                Key={
                    "PK": {"S": f"TENDER#{tender_id}"},
                    "SK": {"S": "METADATA"},
                },
                UpdateExpression="SET #status = :status, updated_at = :updated_at, GSI1PK = :gsi1pk, GSI1SK = :gsi1sk",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": {"S": status.value},
                    ":updated_at": {"S": datetime.utcnow().isoformat()},
                    ":gsi1pk": {"S": f"STATUS#{status.value}"},
                    ":gsi1sk": {"S": datetime.utcnow().isoformat()},
                },
            )
            logger.info(f"Updated tender {tender_id} status to {status.value}")
            return True

        except ClientError as e:
            logger.error(f"Failed to update tender {tender_id} status: {e}")
            return False
