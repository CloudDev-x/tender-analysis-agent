# =============================================================================
# Bedrock Service
# =============================================================================

import json
import logging
from typing import Optional

from botocore.exceptions import ClientError

from ..config import get_bedrock_client, get_settings

logger = logging.getLogger(__name__)


class BedrockService:
    """Bedrock model invocation."""

    def __init__(self) -> None:
        self.client = get_bedrock_client()
        self.settings = get_settings()

    def invoke_model(self, prompt: str, system: Optional[str] = None, max_tokens: int = 2000) -> Optional[str]:
        """
        Invoke Claude Haiku model.
        Returns generated text or None on failure.
        """
        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "modelId": self.settings.BEDROCK_INFERENCE_MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
            }

            if system:
                kwargs["system"] = system

            response = self.client.invoke_model(**kwargs)
            response_body = json.loads(response["body"].read())
            
            # Extract text from response
            if "content" in response_body and response_body["content"]:
                text = response_body["content"][0].get("text", "")
                logger.debug(f"Bedrock invocation succeeded ({len(text)} chars)")
                return text

            logger.warning("Bedrock response had no content")
            return None

        except ClientError as e:
            logger.error(f"Bedrock invocation failed: {e}")
            return None
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse Bedrock response: {e}")
            return None

    def invoke_model_with_json(self, prompt: str, system: Optional[str] = None, max_tokens: int = 2000) -> Optional[dict]:
        """
        Invoke Claude Haiku and parse response as JSON.
        Returns parsed dict or None on failure.
        """
        text = self.invoke_model(prompt, system=system, max_tokens=max_tokens)
        if text is None:
            return None

        try:
            # Try to parse as JSON
            json_text = text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]  # Remove ```json
            if json_text.startswith("```"):
                json_text = json_text[3:]  # Remove ```
            if json_text.endswith("```"):
                json_text = json_text[:-3]  # Remove closing ```
            
            return json.loads(json_text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bedrock JSON response: {e}")
            logger.debug(f"Response was: {text[:200]}...")
            return None

    def count_tokens_estimate(self, text: str) -> int:
        """
        Rough estimate of token count.
        Actual count may vary; for estimation only.
        ~1 token per 4 characters for English text.
        """
        return max(1, len(text) // 4)
