# =============================================================================
# Mayzerock Tender System — Production Environment
# =============================================================================

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(var.tags, {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    })
  }
}

# -----------------------------------------------------------------------------
# Data sources
# -----------------------------------------------------------------------------
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# -----------------------------------------------------------------------------
# KMS — single application key for V1
# -----------------------------------------------------------------------------
module "kms" {
  source = "../../modules/kms"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
  account_id   = data.aws_caller_identity.current.account_id
}

# -----------------------------------------------------------------------------
# S3 — tender bucket + evidence bucket
# -----------------------------------------------------------------------------
module "s3" {
  source = "../../modules/s3"

  project_name = var.project_name
  environment  = var.environment
  kms_key_arn  = module.kms.key_arn
}

# -----------------------------------------------------------------------------
# DynamoDB — single-table design
# -----------------------------------------------------------------------------
module "dynamodb" {
  source = "../../modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment
  kms_key_arn  = module.kms.key_arn
}

# -----------------------------------------------------------------------------
# IAM — per-function roles
# -----------------------------------------------------------------------------
module "iam" {
  source = "../../modules/iam"

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = data.aws_region.current.name
  account_id         = data.aws_caller_identity.current.account_id
  tender_bucket_arn  = module.s3.tender_bucket_arn
  evidence_bucket_arn = module.s3.evidence_bucket_arn
  dynamodb_table_arn = module.dynamodb.table_arn
  kms_key_arn        = module.kms.key_arn

  bedrock_inference_model_id = var.bedrock_inference_model_id
}

# -----------------------------------------------------------------------------
# Lambda — function definitions (Phase 3+)
# -----------------------------------------------------------------------------
# module "lambda" {
#   source = "../../modules/lambda"
#   ...
# }

# -----------------------------------------------------------------------------
# Step Functions — workflow orchestration (Phase 4+)
# -----------------------------------------------------------------------------
# module "step_functions" {
#   source = "../../modules/step-functions"
#   ...
# }

# -----------------------------------------------------------------------------
# Bedrock — Knowledge Base + S3 Vectors (Phase 6+)
# -----------------------------------------------------------------------------
# module "bedrock" {
#   source = "../../modules/bedrock"
#   ...
# }

# -----------------------------------------------------------------------------
# SES — notifications (Phase 10+)
# -----------------------------------------------------------------------------
# module "ses" {
#   source = "../../modules/ses"
#   ...
# }

# -----------------------------------------------------------------------------
# CloudWatch + Budgets (Phase 11+)
# -----------------------------------------------------------------------------
module "cloudwatch" {
  source = "../../modules/cloudwatch"

  project_name = var.project_name
  environment  = var.environment
}

module "budgets" {
  source = "../../modules/budgets"

  project_name       = var.project_name
  budget_limit       = var.budget_limit
  alert_thresholds   = var.budget_alert_thresholds
  alert_emails       = var.budget_alert_emails
}
