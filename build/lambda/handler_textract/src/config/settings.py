# =============================================================================
# Settings — Environment Configuration
# =============================================================================

import os
from functools import lru_cache


class Settings:
    """Application configuration from environment variables."""

    # AWS
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCOUNT_ID: str = os.getenv("AWS_ACCOUNT_ID", "524547833635")

    # S3
    TENDER_BUCKET: str = os.getenv("TENDER_BUCKET", "mayzerock-tender-tenders-prod")
    EVIDENCE_BUCKET: str = os.getenv("EVIDENCE_BUCKET", "mayzerock-tender-evidence-prod")

    # S3 Prefixes
    S3_INCOMING_PREFIX: str = "incoming"
    S3_PROCESSING_PREFIX: str = "processing"
    S3_OUTPUTS_PREFIX: str = "outputs"
    S3_AUDIT_PREFIX: str = "audit"
    S3_FAILED_PREFIX: str = "failed"

    # DynamoDB
    DYNAMODB_TABLE: str = os.getenv("DYNAMODB_TABLE", "mayzerock-tender-prod")

    # KMS
    KMS_KEY_ARN: str = os.getenv(
        "KMS_KEY_ARN",
        "arn:aws:kms:us-east-1:524547833635:key/d573e7b5-5a16-4354-9357-0758abd92588"
    )

    # Bedrock
    BEDROCK_REGION: str = os.getenv("BEDROCK_REGION", "us-east-1")
    BEDROCK_INFERENCE_MODEL: str = os.getenv(
        "BEDROCK_INFERENCE_MODEL",
        "us.anthropic.claude-3-haiku-20240307-v1:0"
    )
    BEDROCK_EMBEDDING_MODEL: str = os.getenv(
        "BEDROCK_EMBEDDING_MODEL",
        "amazon.titan-embed-text-v2:0"
    )
    BEDROCK_KB_ID: str = os.getenv("BEDROCK_KB_ID", "")  # Set after KB creation

    # SES
    SES_SENDER_EMAIL: str = os.getenv("SES_SENDER_EMAIL", "tenders@mayzerock.com")
    SES_REGION: str = os.getenv("SES_REGION", "us-east-1")

    # Textract
    TEXTRACT_REGION: str = os.getenv("TEXTRACT_REGION", "us-east-1")

    # Application
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "prod")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Thresholds
    EXTRACTION_CONFIDENCE_THRESHOLD: float = 0.85
    RETRIEVAL_SCORE_THRESHOLD: float = 0.70
    OCR_CONFIDENCE_THRESHOLD: float = 0.80

    # Timeouts
    TEXTRACT_POLL_TIMEOUT_SECONDS: int = 900  # 15 minutes
    TEXTRACT_POLL_INTERVAL_SECONDS: int = 5
    BEDROCK_TIMEOUT_SECONDS: int = 60

    # Bedrock retry
    BEDROCK_MAX_RETRIES: int = 2
    BEDROCK_RETRY_BACKOFF: float = 1.5


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
