# =============================================================================
# Compliance Repository
# =============================================================================

import json
import logging
from datetime import datetime
from typing import Optional

from botocore.exceptions import ClientError

from ..config import get_dynamodb_client, get_settings
from ..models.compliance import ComplianceAssessment, ComplianceStatus, ComplianceSummary

logger = logging.getLogger(__name__)


class ComplianceRepository:
    """DynamoDB queries for compliance assessments."""

    def __init__(self) -> None:
        self.client = get_dynamodb_client()
        self.settings = get_settings()
        self.table_name = self.settings.DYNAMODB_TABLE

    def put_assessment(self, tender_id: str, assessment: ComplianceAssessment) -> bool:
        """Store a single compliance assessment."""
        try:
            item = {
                "PK": {"S": f"TENDER#{tender_id}"},
                "SK": {"S": f"COMPLIANCE#{assessment.requirement_id}"},
                "requirement_id": {"S": assessment.requirement_id},
                "status": {"S": assessment.status.value},
                "reason": {"S": assessment.reason},
                "confidence": {"N": str(assessment.confidence)},
                "human_review_required": {"BOOL": assessment.human_review_required},
                "assessed_at": {"S": assessment.assessed_at.isoformat()},
            }

            if assessment.evidence:
                evidence_dict = assessment.evidence.dict()
                item["evidence"] = {"S": json.dumps(evidence_dict, default=str)}

            if assessment.review_reason:
                item["review_reason"] = {"S": assessment.review_reason}

            self.client.put_item(TableName=self.table_name, Item=item)
            logger.debug(f"Stored compliance assessment for {tender_id}/{assessment.requirement_id}")
            return True

        except ClientError as e:
            logger.error(f"Failed to put compliance assessment: {e}")
            return False

    def get_assessment(self, tender_id: str, requirement_id: str) -> Optional[ComplianceAssessment]:
        """Retrieve a single compliance assessment."""
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={
                    "PK": {"S": f"TENDER#{tender_id}"},
                    "SK": {"S": f"COMPLIANCE#{requirement_id}"},
                },
            )

            if "Item" not in response:
                return None

            item = response["Item"]
            assessment = ComplianceAssessment(
                requirement_id=item["requirement_id"]["S"],
                status=ComplianceStatus(item["status"]["S"]),
                reason=item["reason"]["S"],
                confidence=float(item["confidence"]["N"]),
                human_review_required=item.get("human_review_required", {}).get("BOOL", False),
                review_reason=item.get("review_reason", {}).get("S"),
                assessed_at=datetime.fromisoformat(item["assessed_at"]["S"]),
            )

            if "evidence" in item:
                assessment.evidence = json.loads(item["evidence"]["S"])

            return assessment

        except ClientError as e:
            logger.error(f"Failed to get compliance assessment: {e}")
            return None

    def get_all_assessments(self, tender_id: str) -> list[ComplianceAssessment]:
        """Retrieve all compliance assessments for a tender."""
        try:
            response = self.client.query(
                TableName=self.table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"TENDER#{tender_id}"},
                    ":sk": {"S": "COMPLIANCE#"},
                },
            )

            assessments = []
            for item in response.get("Items", []):
                assessment = ComplianceAssessment(
                    requirement_id=item["requirement_id"]["S"],
                    status=ComplianceStatus(item["status"]["S"]),
                    reason=item["reason"]["S"],
                    confidence=float(item["confidence"]["N"]),
                    human_review_required=item.get("human_review_required", {}).get("BOOL", False),
                    review_reason=item.get("review_reason", {}).get("S"),
                    assessed_at=datetime.fromisoformat(item["assessed_at"]["S"]),
                )
                if "evidence" in item:
                    assessment.evidence = json.loads(item["evidence"]["S"])
                assessments.append(assessment)

            logger.info(f"Retrieved {len(assessments)} compliance assessments for {tender_id}")
            return assessments

        except ClientError as e:
            logger.error(f"Failed to get all compliance assessments: {e}")
            return []

    def get_summary(self, tender_id: str) -> ComplianceSummary:
        """Get compliance summary for a tender."""
        assessments = self.get_all_assessments(tender_id)
        summary = ComplianceSummary(tender_id=tender_id, assessments=assessments)
        summary.update_counts()
        return summary
