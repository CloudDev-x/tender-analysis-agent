# Mayzerock AI Tender Analysis & Bid Drafting System

An **AWS serverless agent** that automates RFP/tender document analysis, compliance checking, and bid brief generation for Mayzerock's services team. Transforms tender PDFs into structured bid briefs within hours — ready for human review and submission.

---

## Problem

Mayzerock receives 500–1,000 tenders annually across its service lines:
- Cloud Infrastructure & Migration
- Managed IT Services  
- Cybersecurity Services
- Software Development
- Data & AI Services
- DevOps & Automation
- Compliance & Governance

**Status quo**: Manual document analysis (2–3 days per tender)
- Read RFP, extract scope/requirements/deadlines
- Check against Mayzerock capabilities and certifications
- Flag compliance gaps (ISO 27001, GDPR, etc.)
- Draft bid brief for senior review
- High risk of missed deadlines, inconsistent assessments

**This system**: Upload PDF → 2–4 hours → structured bid brief ready for bid team.

---

## Impact & ROI

- **Analysis time**: 2–3 days → 4 hours per tender (80% reduction)
- **Team capacity**: 1 bid analyst freed from document parsing per tender
- **Consistency**: Deterministic compliance matching eliminates human interpretation variance
- **Risk**: Gaps flagged automatically; no missed deadlines or overlooked requirements
- **Cost savings**: 1 analyst @ £50k/year = ~£2,000/week → system cost ($450/month) pays for itself in **< 1 week**
- **Annual impact**: 500 tenders × 2.5 days saved = 1,250 analyst-days = **~£625k labor savings**

---

## Solution

1. **Upload tender PDF** to S3
2. **Extract requirements** via Textract + Claude Bedrock
3. **Cross-reference capabilities** — Bedrock Knowledge Base searches Mayzerock's:
   - 40+ completed cloud migration projects
   - ISO 27001, CREST, CHECK, OSCP certifications
   - 25 bespoke software projects
   - Service line expertise (DevOps, cybersecurity, data/AI, managed services)
4. **Deterministic compliance matching** — DynamoDB holds Mayzerock's certifications, capabilities, project history
5. **Risk analysis** — Claude identifies gaps, timeline risk, financial exposure
6. **Bid brief generation** — GO / CONDITIONAL / NO_GO recommendation + compliance checklist
7. **Human review** — Bid team reviews and finalizes (system never auto-submits)

---

## Architecture

```
Tender PDF
    ↓
S3 + Step Functions (15 states)
    ↓
[Textract OCR] → [Quality Gate] → [Normalize Text]
    ↓
[Extract Requirements] → [Retrieve Evidence from KB] → [Compliance Engine]
    ↓
[Risk Analysis] → [Bid Drafting] → [Validate & Persist]
    ↓
[SES Notification] → Human Review
```

**Key services**:
- **Bedrock**: Claude Haiku for requirement extraction, risk analysis, bid generation
- **Bedrock Knowledge Bases + OpenSearch Serverless**: Semantic search across Mayzerock capabilities
- **Textract**: PDF text extraction (handles scanned documents)
- **Step Functions**: 15-state workflow with error handling and manual review gates
- **DynamoDB**: Single-table design (25 Mayzerock records: certifications, capabilities, projects, personnel)
- **Lambda**: 14 functions (intake, extraction, compliance, risk, drafting, persistence, notification)
- **S3**: Tender + evidence buckets (KMS-encrypted)
- **KMS, IAM, CloudWatch**: Security, least-privilege, observability

---

## Key Design Decisions

### Deterministic Compliance Matching (No LLM in Critical Path)
Requirements are extracted via Claude. **Compliance decisions come from pure DynamoDB logic**:

```
Requirement: ISO 27001 certification
DynamoDB lookup: CERT#ISO27001 (status: ACTIVE, expires: 2027-06-30)
Result: MET (expires > today) or EXPIRED (expires < today)
```

**Trade-off**: 
- ❌ LLM-based matching: Cheaper, more flexible, but non-deterministic (hallucination risk)
- ✓ Deterministic DynamoDB: Slightly more overhead, but auditable and 100% reliable

**Why this matters**: Compliance is binary. A missed certification or hallucinated match could cost Mayzerock a bid or create liability. Single source of truth (DynamoDB) = traceability for auditors.

### OpenSearch Serverless for Evidence Retrieval (Not Compliance)
Bedrock Knowledge Base retrieves supporting evidence (project history, certifications, personnel). **Used only for context**, not compliance decisions.

**Trade-off**:
- ❌ S3 Vectors: Free, but lose semantic search; compliance matching would fall back to LLM scoring (risky)
- ✓ OpenSearch Serverless: +$175–350/month, but enables rich semantic search + keeps compliance deterministic

**Why this matters**: Semantic search lets bid team see relevant past projects ("You did this for NHS Digital, client reference available"). But compliance matching stays in DynamoDB. Best of both worlds.

### Manual Review Gate for Poor OCR
Confidence < 0.80 triggers human review before downstream processing.

**Why**: Scanned PDFs can corrupt extraction. Early gate prevents bad data from poisoning bid brief.

### Never Auto-Submit
System generates GO/CONDITIONAL/NO_GO briefs. Humans make final submission decisions.

**Why**: Bid strategy is commercial. System flags risks; bid team decides.

---

## Cost & Business Case

| Service | Monthly Estimate |
|---|---|
| OpenSearch Serverless | $175–350 |
| Textract (3,000 pages) | ~$4.50 |
| Bedrock (Claude Haiku) | ~$0.40 |
| DynamoDB | ~$1.50 |
| Lambda + Step Functions | ~$0.50 |
| S3, KMS, CloudWatch, SES | ~$3.00 |
| **Total** | **$184–360** |
| **Budget ceiling** | **$450/month** |

**Business case**: 
- System cost: ~$5,400/year ($450/month × 12)
- Analyst labor saved: ~£625k/year (500 tenders × 2.5 days × £400/day)
- **Net ROI: 115× cost** (system pays for itself in < 1 week)

Supports up to ~3,500 tenders/month before exceeding ceiling. See `COSTS.md` for detailed breakdown.

---

## Deployment

### Prerequisites
- AWS Account with appropriate IAM permissions
- Terraform >= 1.0
- Python 3.11+
- AWS CLI v2 configured

### Quick Start
```bash
git clone https://github.com/yourusername/mayzerock-tender-system.git
cd mayzerock-tender-system

# Setup
cp .env.template .env
# Edit .env with your AWS account ID, region, bucket names
source .env

# Build Lambda packages
python scripts/build-lambda-packages.py

# Deploy infrastructure
cd infrastructure/environments/prod
terraform init
terraform apply -auto-approve

# Seed company data
python ../../scripts/seed-dynamodb.py

# Test end-to-end
TENDER_ID="TENDER-$(date +%s)"
aws s3 cp sample-tender.pdf s3://$TENDER_BUCKET/incoming/${TENDER_ID}/original.pdf

aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input "{\"tender_id\": \"$TENDER_ID\", \"s3_bucket\": \"$TENDER_BUCKET\", \"s3_key\": \"incoming/$TENDER_ID/original.pdf\"}"
```

See `DEPLOY.md` for detailed walkthrough.

---

## Project Structure

```
mayzerock-tender-system/
├── src/                          # Python application code
│   ├── config/                   # AWS clients, settings
│   ├── models/                   # Data models (Tender, Requirement, Compliance, Risk)
│   ├── services/                 # Business logic (S3, Textract, Bedrock, KB)
│   ├── repositories/             # DynamoDB access
│   ├── handlers/                 # 14 Lambda functions
│   └── prompts/                  # Claude system prompts
├── infrastructure/               # Terraform
│   ├── modules/                  # Reusable modules (KMS, S3, DynamoDB, Lambda, Bedrock, etc.)
│   └── environments/prod/        # Production configuration
├── scripts/                      # Utility scripts (build, seed, deploy)
├── docs/                         # Documentation
│   └── architecture.html         # Visual architecture diagram
├── .gitignore
├── .env.template
├── README.md                     # This file

```

---

## Monitoring & Debugging

### CloudWatch Logs
```bash
# View logs for a specific tender
aws logs filter-log-events \
  --log-group-name /aws/stepfunctions/mayzerock-tender-workflow-prod \
  --filter-pattern $TENDER_ID
```

### Check bid brief output
```bash
aws s3 cp s3://$TENDER_BUCKET/outputs/${TENDER_ID}/bid_brief.json .
cat bid_brief.json | jq .
```

### Budget alerts
6 thresholds trigger SNS notifications: $150, $200, $250, $300, $375, $450.

---

## Security

- **S3 encryption**: KMS (customer-managed key)
- **DynamoDB encryption**: KMS
- **IAM**: Least-privilege (14 Lambda roles + 1 Step Functions role, 76 policies total)
- **Secrets**: Use AWS Secrets Manager for SES credentials
- **Audit**: CloudTrail logs S3 operations, CloudWatch logs all Lambda/Step Functions activity

---

## Known Limitations

1. **SES requires manual verification** — Sender/recipient emails must be verified in SES console
2. **No concurrent tender limits** — Add Step Functions rate limiting if needed
3. **Manual KB refresh** — Bedrock Knowledge Base must be re-ingested when company capabilities change
4. **Bedrock access required** — Models are opt-in; request access in AWS console

---



## Questions?

See `DEPLOY.md` for setup details, `COSTS.md` for cost breakdown, or the architecture diagram in `docs/`.
