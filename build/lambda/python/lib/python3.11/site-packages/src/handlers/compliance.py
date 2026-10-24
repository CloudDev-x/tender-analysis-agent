"""
Handler: Compliance Assessment
Step 10 in Step Functions workflow
Deterministic compliance logic: matches requirements against DynamoDB company facts
Input: Requirements, evidence
Output: Compliance assessments
"""

import json
import logging
from datetime import datetime
from typing import Any

from src.repositories.tender_repository import TenderRepository
from src.repositories.compliance_repository import ComplianceRepository
from src.models.compliance import ComplianceStatus, ComplianceAssessment

logger = logging.getLogger(__name__)


def assess_compliance(requirement: dict, company_record: dict) -> ComplianceStatus:
    """
    Deterministic compliance logic.
    
    Returns: MET, PARTIAL, GAP, EXPIRED, UNKNOWN, NOT_APPLICABLE
    """
    req_category = requirement.get("category", "")
    req_desc = requirement.get("description", "")
    
    # Company record contains: CERT#, CAP#, PROJ#, PERS# attributes
    # Example: company_record["certifications"] = [{name: "ISO 9001", status: "ACTIVE", expiry: "2027-12-31"}]
    
    if not req_desc:
        return ComplianceStatus.UNKNOWN
    
    # Simple example: if requirement mentions "ISO" and company has active ISO cert
    if "ISO" in req_desc.upper():
        certs = company_record.get("certifications", [])
        for cert in certs:
            if "ISO" in cert.get("name", "").upper():
                expiry = cert.get("expiry")
                if expiry:
                    expiry_dt = datetime.fromisoformat(expiry)
                    if expiry_dt > datetime.now():
                        return ComplianceStatus.MET
                    else:
                        return ComplianceStatus.EXPIRED
        return ComplianceStatus.GAP
    
    # Default: no company record match
    return ComplianceStatus.UNKNOWN


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Run deterministic compliance assessment.
    
    Args:
        event: {"tender_id": "...", "company_id": "MAYZEROCK"}
        context: Lambda context
    
    Returns:
        {
            "tender_id": "...",
            "assessments_created": int,
            "met_count": int,
            "gap_count": int,
            "status": "SUCCESS"
        }
    """
    try:
        tender_id = event.get("tender_id")
        company_id = event.get("company_id", "MAYZEROCK")
        
        logger.info(f"Assessing compliance for {tender_id}")
        
        # Get tender requirements
        tender_repo = TenderRepository()
        tender = tender_repo.get_tender_record(tender_id=tender_id)
        requirements = tender.get("requirements", [])
        
        # Get company record
        company = tender_repo.get_company_record(company_id=company_id)
        
        # Assess each requirement
        compliance_repo = ComplianceRepository()
        assessments = []
        
        counts = {"met": 0, "partial": 0, "gap": 0, "expired": 0, "unknown": 0}
        
        for i, req in enumerate(requirements):
            status = assess_compliance(req, company)
            counts[status.value.lower()] = counts.get(status.value.lower(), 0) + 1
            
            assessment = ComplianceAssessment(
                requirement_id=f"REQ-{i}",
                requirement_description=req.get("description", ""),
                status=status,
                evidence_source="DETERMINISTIC",
                assessed_at=datetime.utcnow().isoformat(),
                notes=f"Assessed against company {company_id} records"
            )
            
            compliance_repo.put_compliance_assessment(assessment)
            assessments.append(assessment)
        
        # Store summary
        tender_repo.update_tender_record(
            tender_id=tender_id,
            updates={
                "compliance_summary": {
                    "total_requirements": len(requirements),
                    "met": counts.get("met", 0),
                    "partial": counts.get("partial", 0),
                    "gap": counts.get("gap", 0),
                    "expired": counts.get("expired", 0),
                    "unknown": counts.get("unknown", 0)
                }
            }
        )
        
        logger.info(f"Compliance assessment complete: {counts}")
        
        return {
            "tender_id": tender_id,
            "assessments_created": len(assessments),
            "met_count": counts.get("met", 0),
            "gap_count": counts.get("gap", 0),
            "status": "SUCCESS"
        }
    
    except Exception as e:
        logger.error(f"Error assessing compliance: {str(e)}")
        return {
            "tender_id": event.get("tender_id"),
            "status": "FAILED",
            "error": str(e)
        }
