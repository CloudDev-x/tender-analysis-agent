"""
Handler: Notification
Step 15 in Step Functions workflow
Sends SES email notification with bid brief summary
Input: Tender record with results
Output: Email sent notification
"""

import json
import logging
from typing import Any

from src.config.aws_clients import get_ses_client, get_dynamodb_client
from src.repositories.tender_repository import TenderRepository

logger = logging.getLogger(__name__)


def format_email_body(tender: dict) -> str:
    """
    Format tender results for email notification.
    
    Returns: HTML email body
    """
    tender_id = tender.get("tender_id", "UNKNOWN")
    metadata = tender.get("metadata", {})
    brief = tender.get("bid_brief", {})
    recommendation = tender.get("bid_recommendation", "CONDITIONAL")
    confidence = tender.get("bid_confidence", 0.0)
    
    compliance = tender.get("compliance_summary", {})
    risks = tender.get("risk_summary", {})
    
    html = f"""
    <html>
    <head><style>
        body {{ font-family: Arial, sans-serif; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; }}
        .section {{ margin: 20px 0; padding: 10px; border-left: 4px solid #3498db; }}
        .recommendation {{ font-size: 18px; font-weight: bold; }}
        .metric {{ display: inline-block; margin: 10px; }}
    </style></head>
    <body>
    <div class="header">
        <h1>Bid Brief: {tender_id}</h1>
        <p>{metadata.get("tender_name", "N/A")}</p>
    </div>
    
    <div class="section">
        <h2>Recommendation: <span class="recommendation">{recommendation}</span></h2>
        <p>Confidence: {confidence:.0%}</p>
    </div>
    
    <div class="section">
        <h3>Compliance Status</h3>
        <div class="metric">Met: {compliance.get("met", 0)}</div>
        <div class="metric">Gaps: {compliance.get("gap", 0)}</div>
        <div class="metric">Expired: {compliance.get("expired", 0)}</div>
    </div>
    
    <div class="section">
        <h3>Risk Summary</h3>
        <div class="metric">High: {risks.get("high", 0)}</div>
        <div class="metric">Medium: {risks.get("medium", 0)}</div>
        <div class="metric">Low: {risks.get("low", 0)}</div>
    </div>
    
    <div class="section">
        <p><strong>Executive Summary:</strong></p>
        <p>{brief.get("executive_summary", "N/A")}</p>
    </div>
    
    <div class="section">
        <p><em>This is an automated bid brief. Please review the full analysis in the Mayzerock Tender System.</em></p>
    </div>
    </body>
    </html>
    """
    
    return html


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Send SES notification email.
    
    Args:
        event: {
            "tender_id": "...",
            "recipient_email": "user@mayzerock.com"
        }
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "message_id": "...",
            "status": "SUCCESS"
        }
    """
    try:
        tender_id = event.get("tender_id")
        recipient_email = event.get("recipient_email", "bids@mayzerock.com")
        
        logger.info(f"Sending notification for {tender_id} to {recipient_email}")
        
        # Get tender record
        repo = TenderRepository()
        tender = repo.get_tender_record(tender_id=tender_id)
        
        # Format email
        email_body = format_email_body(tender)
        
        # Send SES email
        ses = get_ses_client()
        response = ses.send_email(
            Source="noreply@mayzerock.com",
            Destination={"ToAddresses": [recipient_email]},
            Message={
                "Subject": {"Data": f"Bid Brief: {tender_id}"},
                "Body": {"Html": {"Data": email_body}}
            }
        )
        
        message_id = response.get("MessageId")
        logger.info(f"Email sent: {message_id}")
        
        return {
            "tender_id": tender_id,
            "message_id": message_id,
            "recipient": recipient_email,
            "status": "SUCCESS"
        }
    
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e)
        }
