# =============================================================================
# KMS — Single customer-managed key for V1
# =============================================================================

variable "project_name" { type = string }
variable "environment" { type = string }
variable "aws_region" { type = string }
variable "account_id" { type = string }

resource "aws_kms_key" "app" {
  description             = "${var.project_name}-${var.environment} application encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "${var.project_name}-${var.environment}-key-policy"
    Statement = [
      {
        Sid    = "EnableRootAccountAccess"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowKeyAdministration"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.account_id}:root"
        }
        Action = [
          "kms:Create*",
          "kms:Describe*",
          "kms:Enable*",
          "kms:List*",
          "kms:Put*",
          "kms:Update*",
          "kms:Revoke*",
          "kms:Disable*",
          "kms:Get*",
          "kms:Delete*",
          "kms:TagResource",
          "kms:UntagResource",
          "kms:ScheduleKeyDeletion",
          "kms:CancelKeyDeletion"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_alias" "app" {
  name          = "alias/${var.project_name}-${var.environment}"
  target_key_id = aws_kms_key.app.key_id
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "key_arn" {
  description = "KMS key ARN"
  value       = aws_kms_key.app.arn
}

output "key_id" {
  description = "KMS key ID"
  value       = aws_kms_key.app.key_id
}

output "alias_arn" {
  description = "KMS key alias ARN"
  value       = aws_kms_alias.app.arn
}
