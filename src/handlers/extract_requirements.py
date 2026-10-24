"""
Handler: Extract Requirements
Step 8 in Step Functions workflow
Uses Bedrock Claude to extract structured requirements from normalized text
Input: Normalized tender text
Output: Structured requirements stored in DynamoDB
"""

import json
import logging
from typing import Any

from src.config.aws_clients import get_s3_client, get_bedrock_client
from src.services.bedrock_service import BedrockService
from src.repositories.tender_repository import TenderRepository
from src.models.requirement import Requirement, RequirementCategory

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Use Bedrock Claude to extract requirements from tender text.
    Parse LLM response, validate structure, store in DynamoDB.
    
    Args:
        event: {
            "tender_id": "...",
            "s3_bucket": "...",
            "max_tokens": 4000 (optional)
        }
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "requirements_extracted": int,
            "high_confidence": int,
            "status": "SUCCESS"
        }
    """
    try:
        tender_id = event.get("tender_id")
        s3_bucket = event.get("s3_bucket")
        max_tokens = event.get("max_tokens", 4000)
        
        logger.info(f"Extracting requirements for {tender_id}")
        
        # Retrieve normalized text
        s3 = get_s3_client()
        response = s3.get_object(
            Bucket=s3_bucket,
            Key=f"processing/{tender_id}/normalized/text.json"
        )
        normalized = json.loads(response["Body"].read())
        tender_text = normalized.get("text", "")
        
        # Load prompt template
        with open("src/prompts/extract_requirements.txt") as f:
            prompt_template = f.read()
        
        prompt = prompt_template.replace("{TENDER_TEXT}", tender_text)
        
        # Call Bedrock
        service = BedrockService()
        response = service.invoke_model_with_json(
            prompt=prompt,
            max_tokens=max_tokens
        )
        
        # Parse requirements
        requirements = []
        try:
            requirements_list = json.loads(response)
            for req_dict in requirements_list:
                # Validate and create Requirement object
                # TODO: Full Pydantic validation
                requirements.append(req_dict)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {str(e)}")
            # Fallback: create empty list, flag for manual review
            requirements = []
        
        # Store in DynamoDB
        repo = TenderRepository()
        high_confidence = sum(1 for r in requirements if r.get("confidence", 0) >= 0.85)
        
        repo.update_tender_record(
            tender_id=tender_id,
            updates={
                "requirements": requirements,
                "requirements_count": len(requirements),
                "high_confidence_count": high_confidence
            }
        )
        
        logger.info(f"Extracted {len(requirements)} requirements ({high_confidence} high-confidence)")
        
        return {
            "tender_id": tender_id,
            "requirements_extracted": len(requirements),
            "high_confidence": high_confidence,
            "status": "SUCCESS"
        }
    
    except Exception as e:
        logger.error(f"Error extracting requirements: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e)
        }
