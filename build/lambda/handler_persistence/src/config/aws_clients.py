# =============================================================================
# AWS Clients — Boto3 Initialization
# =============================================================================

from functools import lru_cache
from typing import Any

import boto3

from .settings import get_settings


@lru_cache(maxsize=1)
def get_s3_client() -> Any:
    """Get cached S3 client."""
    settings = get_settings()
    return boto3.client("s3", region_name=settings.AWS_REGION)


@lru_cache(maxsize=1)
def get_dynamodb_client() -> Any:
    """Get cached DynamoDB client."""
    settings = get_settings()
    return boto3.client("dynamodb", region_name=settings.AWS_REGION)


@lru_cache(maxsize=1)
def get_bedrock_client() -> Any:
    """Get cached Bedrock runtime client."""
    settings = get_settings()
    return boto3.client("bedrock-runtime", region_name=settings.BEDROCK_REGION)


@lru_cache(maxsize=1)
def get_bedrock_agent_client() -> Any:
    """Get cached Bedrock agent runtime client (for Knowledge Base retrieval)."""
    settings = get_settings()
    return boto3.client("bedrock-agent-runtime", region_name=settings.BEDROCK_REGION)


@lru_cache(maxsize=1)
def get_textract_client() -> Any:
    """Get cached Textract client."""
    settings = get_settings()
    return boto3.client("textract", region_name=settings.TEXTRACT_REGION)


@lru_cache(maxsize=1)
def get_ses_client() -> Any:
    """Get cached SES client."""
    settings = get_settings()
    return boto3.client("ses", region_name=settings.SES_REGION)


@lru_cache(maxsize=1)
def get_kms_client() -> Any:
    """Get cached KMS client."""
    settings = get_settings()
    return boto3.client("kms", region_name=settings.AWS_REGION)
