# =============================================================================
# Textract Service
# =============================================================================

import logging
import time
from typing import Optional

from botocore.exceptions import ClientError

from ..config import get_textract_client, get_settings

logger = logging.getLogger(__name__)


class TextractService:
    """Textract OCR and text extraction."""

    def __init__(self) -> None:
        self.client = get_textract_client()
        self.settings = get_settings()

    def detect_document_text(self, bucket: str, key: str) -> Optional[dict]:
        """
        Synchronous DetectDocumentText for small documents.
        Returns raw Textract response.
        """
        try:
            response = self.client.detect_document_text(
                Document={"S3Object": {"Bucket": bucket, "Name": key}}
            )
            logger.info(f"DetectDocumentText completed for s3://{bucket}/{key}")
            return response
        except ClientError as e:
            logger.error(f"DetectDocumentText failed for s3://{bucket}/{key}: {e}")
            return None

    def start_document_text_detection(self, bucket: str, key: str) -> Optional[str]:
        """
        Asynchronous StartDocumentTextDetection for multi-page documents.
        Returns JobId.
        """
        try:
            response = self.client.start_document_text_detection(
                DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}}
            )
            job_id = response["JobId"]
            logger.info(f"Started async text detection job {job_id} for s3://{bucket}/{key}")
            return job_id
        except ClientError as e:
            logger.error(f"StartDocumentTextDetection failed for s3://{bucket}/{key}: {e}")
            return None

    def get_document_text_detection(self, job_id: str, next_token: Optional[str] = None) -> Optional[dict]:
        """
        Get results of async text detection job.
        Returns response with JobStatus and Blocks.
        """
        try:
            kwargs = {"JobId": job_id}
            if next_token:
                kwargs["NextToken"] = next_token
            response = self.client.get_document_text_detection(**kwargs)
            return response
        except ClientError as e:
            logger.error(f"GetDocumentTextDetection failed for job {job_id}: {e}")
            return None

    def wait_for_job_completion(self, job_id: str, timeout_seconds: int = 900) -> Optional[dict]:
        """
        Poll job status until completion or timeout.
        Returns final response or None if timeout/error.
        """
        start_time = time.time()
        poll_interval = self.settings.TEXTRACT_POLL_INTERVAL_SECONDS

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.error(f"Timeout waiting for job {job_id} (>{timeout_seconds}s)")
                return None

            response = self.get_document_text_detection(job_id)
            if response is None:
                return None

            status = response.get("JobStatus")
            if status == "SUCCEEDED":
                logger.info(f"Job {job_id} completed successfully")
                return response
            elif status == "FAILED":
                logger.error(f"Job {job_id} failed: {response.get('StatusMessage', 'unknown error')}")
                return None
            elif status == "IN_PROGRESS":
                logger.debug(f"Job {job_id} still in progress... ({elapsed:.1f}s)")
                time.sleep(poll_interval)
            else:
                logger.warning(f"Job {job_id} has unexpected status: {status}")
                time.sleep(poll_interval)

    def extract_text_from_response(self, response: dict) -> str:
        """
        Extract plain text from Textract response.
        Handles both sync and async responses.
        """
        text_lines = []
        blocks = response.get("Blocks", [])

        for block in blocks:
            if block["BlockType"] == "LINE":
                if "Text" in block:
                    text_lines.append(block["Text"])

        return "\n".join(text_lines)

    def extract_text_with_confidence(self, response: dict) -> tuple[str, float]:
        """
        Extract text and compute average confidence.
        Returns (text, confidence).
        """
        text_lines = []
        confidences = []
        blocks = response.get("Blocks", [])

        for block in blocks:
            if block["BlockType"] == "LINE":
                if "Text" in block:
                    text_lines.append(block["Text"])
                    if "Confidence" in block:
                        confidences.append(block["Confidence"])

        text = "\n".join(text_lines)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return text, avg_confidence
