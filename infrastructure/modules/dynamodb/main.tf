# =============================================================================
# DynamoDB — Single-table design
# =============================================================================
# Access patterns:
#   PK=TENDER#<id>  SK=METADATA         → tender metadata
#   PK=TENDER#<id>  SK=REQ#<seq>        → individual requirements
#   PK=TENDER#<id>  SK=RISK#<seq>       → risk entries
#   PK=TENDER#<id>  SK=GAP#<seq>        → compliance gaps
#   PK=TENDER#<id>  SK=ANALYSIS         → final analysis summary
#   PK=TENDER#<id>  SK=WORKFLOW         → Step Functions execution state
#   PK=COMPANY#MAYZEROCK  SK=CERT#<id>  → certifications
#   PK=COMPANY#MAYZEROCK  SK=CAP#<id>   → capabilities
#   PK=COMPANY#MAYZEROCK  SK=PROJ#<id>  → project experience
#   PK=COMPANY#MAYZEROCK  SK=PERS#<id>  → personnel
#   PK=COMPANY#MAYZEROCK  SK=PROFILE    → company profile
#
# GSI1: query tenders by status (PROCESSING, COMPLETED, FAILED, REVIEW)
#   GSI1PK=STATUS#<status>  GSI1SK=<submitted_at>
#
# GSI2: query tenders by submission deadline
#   GSI2PK=DEADLINE  GSI2SK=<deadline_date>
# =============================================================================

variable "project_name" { type = string }
variable "environment" { type = string }
variable "kms_key_arn" { type = string }

resource "aws_dynamodb_table" "main" {
  name         = "${var.project_name}-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "GSI1PK"
    type = "S"
  }

  attribute {
    name = "GSI1SK"
    type = "S"
  }

  attribute {
    name = "GSI2PK"
    type = "S"
  }

  attribute {
    name = "GSI2SK"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI1-StatusIndex"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "GSI2-DeadlineIndex"
    hash_key        = "GSI2PK"
    range_key       = "GSI2SK"
    projection_type = "KEYS_ONLY"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  point_in_time_recovery {
    enabled = true
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "table_name" {
  value = aws_dynamodb_table.main.name
}

output "table_arn" {
  value = aws_dynamodb_table.main.arn
}

output "gsi1_arn" {
  value = "${aws_dynamodb_table.main.arn}/index/GSI1-StatusIndex"
}

output "gsi2_arn" {
  value = "${aws_dynamodb_table.main.arn}/index/GSI2-DeadlineIndex"
}
