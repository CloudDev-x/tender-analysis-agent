# =============================================================================
# IAM — Per-function Lambda execution roles
# =============================================================================
# Each Lambda gets its own role scoped to exactly the resources it touches.
# Roles are defined here; additional policies added as modules are enabled.
# =============================================================================

variable "project_name" { type = string }
variable "environment" { type = string }
variable "aws_region" { type = string }
variable "account_id" { type = string }
variable "tender_bucket_arn" { type = string }
variable "evidence_bucket_arn" { type = string }
variable "dynamodb_table_arn" { type = string }
variable "kms_key_arn" { type = string }
variable "bedrock_inference_model_id" { type = string }

locals {
  prefix = "${var.project_name}-${var.environment}"

  # Lambda function names → their required access
  lambda_roles = {
    intake = {
      description = "Validates upload and creates tender record"
      s3_read     = ["${var.tender_bucket_arn}/incoming/*"]
      s3_write    = []
      dynamo      = "write"
    }
    document_profile = {
      description = "Determines document type and Textract mode"
      s3_read     = ["${var.tender_bucket_arn}/incoming/*"]
      s3_write    = []
      dynamo      = "read"
    }
    textract = {
      description = "Starts and checks async Textract jobs"
      s3_read     = ["${var.tender_bucket_arn}/incoming/*"]
      s3_write    = ["${var.tender_bucket_arn}/processing/*"]
      dynamo      = "write"
      textract    = true
    }
    ocr_quality = {
      description = "Validates Textract output quality"
      s3_read     = ["${var.tender_bucket_arn}/processing/*"]
      s3_write    = []
      dynamo      = "write"
    }
    normalize = {
      description = "Normalizes extracted text to internal representation"
      s3_read     = ["${var.tender_bucket_arn}/processing/*"]
      s3_write    = ["${var.tender_bucket_arn}/processing/*"]
      dynamo      = "none"
    }
    extract_requirements = {
      description = "Bedrock Haiku extracts requirements and metadata"
      s3_read     = ["${var.tender_bucket_arn}/processing/*"]
      s3_write    = ["${var.tender_bucket_arn}/processing/*"]
      dynamo      = "write"
      bedrock     = true
    }
    retrieve_evidence = {
      description = "Queries Bedrock KB for matching Mayzerock evidence"
      s3_read     = ["${var.evidence_bucket_arn}/*"]
      s3_write    = []
      dynamo      = "read"
      bedrock_kb  = true
    }
    compliance = {
      description = "Deterministic compliance matching"
      s3_read     = []
      s3_write    = []
      dynamo      = "readwrite"
    }
    risk_analysis = {
      description = "Deterministic risk rules + optional Bedrock narrative"
      s3_read     = []
      s3_write    = []
      dynamo      = "readwrite"
      bedrock     = true
    }
    bid_drafting = {
      description = "Bedrock generates structured bid summary"
      s3_read     = ["${var.tender_bucket_arn}/processing/*"]
      s3_write    = ["${var.tender_bucket_arn}/outputs/*"]
      dynamo      = "read"
      bedrock     = true
    }
    output_validation = {
      description = "Validates final JSON output against schema"
      s3_read     = ["${var.tender_bucket_arn}/outputs/*"]
      s3_write    = []
      dynamo      = "write"
    }
    persistence = {
      description = "Writes final analysis to DynamoDB and S3"
      s3_read     = []
      s3_write    = ["${var.tender_bucket_arn}/outputs/*", "${var.tender_bucket_arn}/audit/*"]
      dynamo      = "write"
    }
    notification = {
      description = "Sends SES notification to bid team"
      s3_read     = ["${var.tender_bucket_arn}/outputs/*"]
      s3_write    = []
      dynamo      = "read"
      ses         = true
    }
    failure_handler = {
      description = "Records failures to audit trail and DynamoDB"
      s3_read     = []
      s3_write    = ["${var.tender_bucket_arn}/failed/*", "${var.tender_bucket_arn}/audit/*"]
      dynamo      = "write"
    }
  }
}

# -----------------------------------------------------------------------------
# Lambda assume-role policy (shared)
# -----------------------------------------------------------------------------
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# -----------------------------------------------------------------------------
# Create one role per Lambda function
# -----------------------------------------------------------------------------
resource "aws_iam_role" "lambda" {
  for_each = local.lambda_roles

  name               = "${local.prefix}-lambda-${each.key}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  description        = each.value.description
}

# -----------------------------------------------------------------------------
# CloudWatch Logs — every Lambda gets basic logging
# -----------------------------------------------------------------------------
resource "aws_iam_role_policy" "lambda_logging" {
  for_each = local.lambda_roles

  name = "cloudwatch-logs"
  role = aws_iam_role.lambda[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:/aws/lambda/${local.prefix}-${each.key}:*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# KMS decrypt — every Lambda that touches encrypted resources
# -----------------------------------------------------------------------------
resource "aws_iam_role_policy" "lambda_kms" {
  for_each = local.lambda_roles

  name = "kms-decrypt"
  role = aws_iam_role.lambda[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = var.kms_key_arn
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# S3 Read policies
# -----------------------------------------------------------------------------
resource "aws_iam_role_policy" "lambda_s3_read" {
  for_each = {
    for k, v in local.lambda_roles : k => v
    if length(v.s3_read) > 0
  }

  name = "s3-read"
  role = aws_iam_role.lambda[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:HeadObject", "s3:ListBucket"]
        Resource = each.value.s3_read
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# S3 Write policies
# -----------------------------------------------------------------------------
resource "aws_iam_role_policy" "lambda_s3_write" {
  for_each = {
    for k, v in local.lambda_roles : k => v
    if length(v.s3_write) > 0
  }

  name = "s3-write"
  role = aws_iam_role.lambda[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:DeleteObject"]
        Resource = each.value.s3_write
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# DynamoDB policies
# -----------------------------------------------------------------------------
resource "aws_iam_role_policy" "lambda_dynamo_read" {
  for_each = {
    for k, v in local.lambda_roles : k => v
    if contains(["read", "readwrite"], v.dynamo)
  }

  name = "dynamodb-read"
  role = aws_iam_role.lambda[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:BatchGetItem"
        ]
        Resource = [
          var.dynamodb_table_arn,
          "${var.dynamodb_table_arn}/index/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_dynamo_write" {
  for_each = {
    for k, v in local.lambda_roles : k => v
    if contains(["write", "readwrite"], v.dynamo)
  }

  name = "dynamodb-write"
  role = aws_iam_role.lambda[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = var.dynamodb_table_arn
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Textract policy
# -----------------------------------------------------------------------------
resource "aws_iam_role_policy" "lambda_textract" {
  for_each = {
    for k, v in local.lambda_roles : k => v
    if lookup(v, "textract", false)
  }

  name = "textract"
  role = aws_iam_role.lambda[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "textract:StartDocumentTextDetection",
          "textract:GetDocumentTextDetection",
          "textract:DetectDocumentText"
        ]
        Resource = "*"
        # Textract does not support resource-level permissions
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Bedrock inference policy
# -----------------------------------------------------------------------------
resource "aws_iam_role_policy" "lambda_bedrock" {
  for_each = {
    for k, v in local.lambda_roles : k => v
    if lookup(v, "bedrock", false)
  }

  name = "bedrock-invoke"
  role = aws_iam_role.lambda[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_inference_model_id}"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Bedrock Knowledge Base retrieve policy
# -----------------------------------------------------------------------------
resource "aws_iam_role_policy" "lambda_bedrock_kb" {
  for_each = {
    for k, v in local.lambda_roles : k => v
    if lookup(v, "bedrock_kb", false)
  }

  name = "bedrock-kb-retrieve"
  role = aws_iam_role.lambda[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["bedrock:Retrieve"]
        Resource = "arn:aws:bedrock:${var.aws_region}:${var.account_id}:knowledge-base/*"
        # Scoped to specific KB ARN once created in Phase 6
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# SES policy
# -----------------------------------------------------------------------------
resource "aws_iam_role_policy" "lambda_ses" {
  for_each = {
    for k, v in local.lambda_roles : k => v
    if lookup(v, "ses", false)
  }

  name = "ses-send"
  role = aws_iam_role.lambda[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Resource = "*"
        # Scoped to verified identity once SES is configured in Phase 10
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Step Functions execution role
# -----------------------------------------------------------------------------
resource "aws_iam_role" "step_functions" {
  name = "${local.prefix}-stepfunctions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "step_functions_invoke_lambda" {
  name = "invoke-lambdas"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = "arn:aws:lambda:${var.aws_region}:${var.account_id}:function:${local.prefix}-*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "lambda_role_arns" {
  description = "Map of Lambda function name to IAM role ARN"
  value = {
    for k, v in aws_iam_role.lambda : k => v.arn
  }
}

output "step_functions_role_arn" {
  description = "Step Functions execution role ARN"
  value       = aws_iam_role.step_functions.arn
}
