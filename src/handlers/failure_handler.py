"""
Handler: Failure Handler
Called when any step in workflow fails
Logs error, updates tender status, sends failure notification
"""

import json
import logging
from typing import Any
from datetime import datetime

from src.config.aws_clients import get_ses_client
from src.repositories.tender_repository import TenderRepository

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handle workflow failures.
    
    Args:
        event: {
            "tender_id": "...",
            "failed_step": "step name",
            "error": "error message",
            "error_type": "...",
            "notify_email": "admin@mayzerock.com" (optional)
        }
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "status": "FAILED",
            "notification_sent": bool
        }
    """
    try:
        tender_id = event.get("tender_id")
        failed_step = event.get("failed_step", "UNKNOWN")
        error = event.get("error", "Unknown error")
        error_type = event.get("error_type", "Exception")
        notify_email = event.get("notify_email", "admin@mayzerock.com")
        
        logger.error(f"Workflow failed for {tender_id} at step {failed_step}: {error}")
        
        # Update tender record
        repo = TenderRepository()
        repo.update_tender_record(
            tender_id=tender_id,
            updates={
                "workflow_status": "FAILED",
                "failed_step": failed_step,
                "failure_reason": error,
                "failure_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Send failure notification
        notification_sent = False
        try:
            ses = get_ses_client()
            response = ses.send_email(
                Source="noreply@mayzerock.com",
                Destination={"ToAddresses": [notify_email]},
                Message={
                    "Subject": {"Data": f"Bid Processing Failed: {tender_id}"},
                    "Body": {
                        "Html": {
                            "Data": f"""
                            <html><body>
                            <h2>Bid Processing Failure</h2>
                            <p><strong>Tender ID:</strong> {tender_id}</p>
                            <p><strong>Failed Step:</strong> {failed_step}</p>
                            <p><strong>Error Type:</strong> {error_type}</p>
                            <p><strong>Error Message:</strong> {error}</p>
                            <p>Please investigate and retry the workflow.</p>
                            </body></html>
                            """
                        }
                    }
                }
            )
            notification_sent = True
            logger.info(f"Failure notification sent: {response.get('MessageId')}")
        
        except Exception as notify_error:
            logger.warning(f"Failed to send failure notification: {str(notify_error)}")
        
        return {
            "tender_id": tender_id,
            "failed_step": failed_step,
            "error": error,
            "status": "FAILED",
            "notification_sent": notification_sent
        }
    
    except Exception as e:
        logger.error(f"Error in failure handler: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e),
            "handler_error": True
        }
