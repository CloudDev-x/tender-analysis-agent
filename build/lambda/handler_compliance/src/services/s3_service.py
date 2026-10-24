# =============================================================================
# S3 Service
# =============================================================================

import json
import logging
from typing import Any, Optional

from botocore.exceptions import ClientError

from ..config import get_s3_client, get_settings

logger = logging.getLogger(__name__)


class S3Service:
    """S3 operations wrapper."""

    def __init__(self) -> None:
        self.client = get_s3_client()
        self.settings = get_settings()

    def upload_file(self, bucket: str, key: str, file_path: str) -> bool:
        """Upload file from local disk to S3."""
        try:
            self.client.upload_file(
                file_path,
                bucket,
                key,
                ExtraArgs={"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": self.settings.KMS_KEY_ARN},
            )
            logger.info(f"Uploaded {file_path} to s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            return False

    def download_file(self, bucket: str, key: str, file_path: str) -> bool:
        """Download file from S3 to local disk."""
        try:
            self.client.download_file(bucket, key, file_path)
            logger.info(f"Downloaded s3://{bucket}/{key} to {file_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download s3://{bucket}/{key}: {e}")
            return False

    def put_object(self, bucket: str, key: str, data: bytes) -> bool:
        """Put object to S3."""
        try:
            self.client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ServerSideEncryption="aws:kms",
                SSEKMSKeyId=self.settings.KMS_KEY_ARN,
            )
            logger.info(f"Put object s3://{bucket}/{key} ({len(data)} bytes)")
            return True
        except ClientError as e:
            logger.error(f"Failed to put object to s3://{bucket}/{key}: {e}")
            return False

    def put_json(self, bucket: str, key: str, data: dict | list) -> bool:
        """Put JSON object to S3."""
        try:
            json_bytes = json.dumps(data, indent=2, default=str).encode("utf-8")
            return self.put_object(bucket, key, json_bytes)
        except Exception as e:
            logger.error(f"Failed to serialize JSON for s3://{bucket}/{key}: {e}")
            return False

    def get_object(self, bucket: str, key: str) -> Optional[bytes]:
        """Get object from S3."""
        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            data = response["Body"].read()
            logger.info(f"Retrieved object s3://{bucket}/{key} ({len(data)} bytes)")
            return data
        except ClientError as e:
            logger.error(f"Failed to get object s3://{bucket}/{key}: {e}")
            return None

    def get_json(self, bucket: str, key: str) -> Optional[dict | list]:
        """Get JSON object from S3."""
        data = self.get_object(bucket, key)
        if data is None:
            return None
        try:
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to parse JSON from s3://{bucket}/{key}: {e}")
            return None

    def list_objects(self, bucket: str, prefix: str) -> list[str]:
        """List objects in bucket with prefix."""
        try:
            response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if "Contents" not in response:
                return []
            return [obj["Key"] for obj in response["Contents"]]
        except ClientError as e:
            logger.error(f"Failed to list objects in s3://{bucket}/{prefix}: {e}")
            return []

    def delete_object(self, bucket: str, key: str) -> bool:
        """Delete object from S3."""
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete s3://{bucket}/{key}: {e}")
            return False

    def object_exists(self, bucket: str, key: str) -> bool:
        """Check if object exists in S3."""
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    def get_object_metadata(self, bucket: str, key: str) -> Optional[dict]:
        """Get object metadata (size, last modified, etc.)."""
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            return {
                "size": response.get("ContentLength", 0),
                "last_modified": response.get("LastModified"),
                "content_type": response.get("ContentType"),
                "version_id": response.get("VersionId"),
            }
        except ClientError as e:
            logger.error(f"Failed to get metadata for s3://{bucket}/{key}: {e}")
            return None
