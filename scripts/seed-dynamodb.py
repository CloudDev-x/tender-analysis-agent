import boto3
import json
from datetime import datetime

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("mayzerock-tender-prod")

items = [
    # Company Profile
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PROFILE",
        "company_name": "Mayzerock",
        "founded": "2019",
        "headquarters": "London, UK",
        "employees": 85,
        "offices": ["London", "Manchester", "Edinburgh"],
        "annual_revenue": "12000000",
        "currency": "GBP",
        "security_clearances": {"SC": 12, "DV": 3},
        "client_retention": "92%",
        "updated_at": datetime.utcnow().isoformat()
    },
    # Certifications
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CERT#ISO9001",
        "name": "ISO 9001:2015",
        "status": "ACTIVE",
        "certificate_number": "QMS-2024-MZ-0451",
        "issuing_body": "BSI Group",
        "issued_date": "2024-03-15",
        "expiry_date": "2027-03-14",
        "scope": "Design, development, and delivery of technology consulting services, cloud infrastructure solutions, and managed IT services"
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CERT#ISO27001",
        "name": "ISO 27001:2022",
        "status": "ACTIVE",
        "certificate_number": "ISMS-2024-MZ-0289",
        "issuing_body": "Bureau Veritas",
        "issued_date": "2024-06-01",
        "expiry_date": "2027-05-31",
        "scope": "Information security management for cloud-hosted applications, client data processing, and IT service delivery"
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CERT#ISO14001",
        "name": "ISO 14001:2015",
        "status": "ACTIVE",
        "certificate_number": "EMS-2023-MZ-0178",
        "issuing_body": "SGS",
        "issued_date": "2023-09-10",
        "expiry_date": "2026-09-09",
        "scope": "Environmental management of office operations and IT infrastructure"
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CERT#CYBERESSENTIALS",
        "name": "Cyber Essentials Plus",
        "status": "ACTIVE",
        "certificate_number": "CEP-2025-MZ-1102",
        "issuing_body": "IASME Consortium",
        "issued_date": "2025-01-20",
        "expiry_date": "2026-01-19",
        "scope": "All internet-facing IT systems and cloud infrastructure"
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CERT#AWS_PARTNER",
        "name": "AWS Partner Network — Advanced Tier",
        "status": "ACTIVE",
        "partner_id": "APN-MZ-2024-ADV",
        "tier": "Advanced",
        "specializations": ["Cloud Migration", "Cloud Operations"],
        "issued_date": "2024-01-01",
        "expiry_date": "2025-12-31"
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CERT#MSFT_GOLD",
        "name": "Microsoft Gold Partner — Cloud Platform",
        "status": "ACTIVE",
        "partner_id": "MSFT-MZ-GP-2024",
        "competency": "Cloud Platform",
        "issued_date": "2024-04-01",
        "expiry_date": "2025-03-31"
    },
    # Capabilities
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CAP#CLOUD_MIGRATION",
        "name": "Cloud Infrastructure & Migration",
        "projects_completed": 40,
        "platforms": ["AWS", "Azure", "GCP"],
        "typical_size": "50-500 VMs",
        "typical_duration": "2-12 months"
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CAP#MANAGED_SERVICES",
        "name": "Managed IT Services",
        "sla_uptime": "99.9%",
        "response_time": "15 minutes",
        "noc_location": "UK",
        "coverage": "24/7"
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CAP#CYBERSECURITY",
        "name": "Cybersecurity Services",
        "certifications": ["CREST", "CHECK", "OSCP"],
        "pentests_per_year": 30,
        "scope": ["web applications", "network infrastructure", "cloud environments"]
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CAP#SOFTWARE_DEV",
        "name": "Software Development",
        "tech_stack": ["Python", "Node.js", "React", ".NET", "Java"],
        "methodology": "Agile/Scrum",
        "projects_delivered": 25
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CAP#DATA_AI",
        "name": "Data & AI Services",
        "services": ["Data lake architecture", "ETL pipelines", "BI dashboards", "ML model deployment"],
        "tools": ["Power BI", "Tableau", "SageMaker", "Databricks"]
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CAP#DEVOPS",
        "name": "DevOps & Automation",
        "tools": ["Terraform", "CloudFormation", "Ansible", "Kubernetes", "ECS"],
        "pipelines_automated": 60
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "CAP#COMPLIANCE",
        "name": "Compliance & Governance",
        "frameworks": ["GDPR", "PCI DSS", "SOC 2", "ISO 27001"],
        "clients_certified": 15
    },
    # Key Projects
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PROJ#NHS_DIGITAL",
        "name": "NHS Digital Cloud Migration",
        "client": "NHS Digital",
        "sector": "Healthcare / Public Sector",
        "duration": "March 2023 – November 2023",
        "value": "1200000",
        "currency": "GBP",
        "scope": "Migration of 120 legacy applications from on-premises to AWS",
        "outcome": "Completed on time, under budget. 99.97% uptime. 35% cost reduction.",
        "technologies": ["AWS EC2", "RDS", "S3", "Lambda", "CloudFront", "Terraform", "Jenkins", "Docker"]
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PROJ#BARCLAYS_API",
        "name": "Barclays API Gateway Platform",
        "client": "Barclays Bank",
        "sector": "Financial Services",
        "duration": "June 2024 – February 2025",
        "value": "800000",
        "currency": "GBP",
        "scope": "Enterprise API gateway platform for Open Banking compliance",
        "outcome": "2M+ API calls/day, 99.99% availability. PCI DSS audit passed first attempt.",
        "technologies": ["AWS API Gateway", "Lambda", "DynamoDB", "CloudWatch", "Kong", "OAuth 2.0", "Python"]
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PROJ#ROLLS_ROYCE_IOT",
        "name": "Rolls-Royce Manufacturing IoT Platform",
        "client": "Rolls-Royce Holdings",
        "sector": "Manufacturing / Aerospace",
        "duration": "January 2024 – August 2024",
        "value": "950000",
        "currency": "GBP",
        "scope": "IoT data ingestion and analytics platform for manufacturing sensor data",
        "outcome": "22% reduction in unplanned downtime. 500K sensor readings/minute.",
        "technologies": ["AWS IoT Core", "Kinesis", "Timestream", "QuickSight", "Python", "Grafana"]
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PROJ#HOME_OFFICE_ID",
        "name": "Home Office Identity Verification System",
        "client": "UK Home Office",
        "sector": "Government / Public Sector",
        "duration": "September 2023 – April 2024",
        "value": "1500000",
        "currency": "GBP",
        "scope": "Cloud-native identity verification for visa processing",
        "outcome": "Processing time reduced from 72hrs to 4hrs. 50K verifications/day.",
        "technologies": ["AWS Textract", "Rekognition", "Step Functions", "SageMaker", "Python", "React"],
        "security_clearance": "SC"
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PROJ#TESCO_ANALYTICS",
        "name": "Tesco Supply Chain Analytics",
        "client": "Tesco PLC",
        "sector": "Retail",
        "duration": "February 2024 – July 2024",
        "value": "450000",
        "currency": "GBP",
        "scope": "Data lake and analytics platform for supply chain optimization",
        "outcome": "Forecast accuracy improved 18%. Stock wastage reduced 12%.",
        "technologies": ["Azure Data Factory", "Synapse", "ML Studio", "Power BI", "Python", "Databricks"]
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PROJ#UNI_MANCHESTER",
        "name": "University of Manchester Research Data Platform",
        "client": "University of Manchester",
        "sector": "Higher Education",
        "duration": "October 2024 – March 2025",
        "value": "320000",
        "currency": "GBP",
        "scope": "Secure research data platform with multi-tenancy and GDPR compliance",
        "outcome": "Data provisioning reduced from 2 weeks to 2 hours. 180 active researchers.",
        "technologies": ["AWS S3", "Athena", "Lake Formation", "SageMaker", "Terraform", "Python"]
    },
    # Key Personnel
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PERS#CEO",
        "name": "Sarah Mitchell",
        "role": "Chief Executive Officer",
        "experience_years": 18,
        "certifications": ["AWS Solutions Architect Professional", "TOGAF 9.2"],
        "qualifications": ["MBA (London Business School)", "BSc Computer Science (Imperial College London)"]
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PERS#CTO",
        "name": "James O'Connor",
        "role": "Chief Technology Officer",
        "experience_years": 15,
        "certifications": ["AWS SA Professional", "AWS DevOps Professional", "CKA"],
        "qualifications": ["MSc Distributed Systems (Edinburgh)", "BEng Software Engineering (Bristol)"]
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PERS#HEAD_SECURITY",
        "name": "Priya Sharma",
        "role": "Head of Cybersecurity",
        "experience_years": 12,
        "certifications": ["OSCP", "CREST", "CISSP", "ISO 27001 Lead Auditor"],
        "qualifications": ["MSc Information Security (Royal Holloway)"]
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PERS#HEAD_CLOUD",
        "name": "David Chen",
        "role": "Head of Cloud Engineering",
        "experience_years": 10,
        "certifications": ["AWS SA Professional", "Azure SA Expert", "Terraform Associate", "ITIL v4"],
        "qualifications": ["BEng Computer Systems Engineering (Warwick)"]
    },
    {
        "PK": "COMPANY#MAYZEROCK",
        "SK": "PERS#HEAD_DATA",
        "name": "Rachel Thompson",
        "role": "Head of Data & AI",
        "experience_years": 8,
        "certifications": ["AWS ML Specialty", "Databricks Data Engineer", "GCP Professional Data Engineer"],
        "qualifications": ["PhD Machine Learning (Cambridge)", "MEng Engineering (Oxford)"]
    }
]

print(f"Seeding {len(items)} records to mayzerock-tender-prod...")

with table.batch_writer() as batch:
    for item in items:
        batch.put_item(Item=item)
        print(f"  ✓ {item['PK']} | {item['SK']}")

print(f"\nDone. {len(items)} records written.")
