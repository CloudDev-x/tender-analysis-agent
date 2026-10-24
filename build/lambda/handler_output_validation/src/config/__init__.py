# =============================================================================
# Configuration Module
# =============================================================================

from .settings import Settings, get_settings
from .aws_clients import get_s3_client, get_dynamodb_client, get_bedrock_client, get_textract_client

__all__ = [
    "Settings",
    "get_settings",
    "get_s3_client",
    "get_dynamodb_client",
    "get_bedrock_client",
    "get_textract_client",
]
