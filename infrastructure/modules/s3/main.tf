# =============================================================================
# S3 — Tender processing bucket + Evidence bucket
# =============================================================================

variable "project_name" { type = string }
variable "environment" { type = string }
variable "kms_key_arn" { type = string }

# -----------------------------------------------------------------------------
# Tender Bucket — stores uploads, processing artifacts, outputs, audit trail
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "tender" {
  bucket        = "${var.project_name}-tenders-${var.environment}"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "tender" {
  bucket = aws_s3_bucket.tender.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tender" {
  bucket = aws_s3_bucket.tender.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "tender" {
  bucket                  = aws_s3_bucket.tender.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "tender_tls_only" {
  bucket = aws_s3_bucket.tender.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.tender.arn,
          "${aws_s3_bucket.tender.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket_lifecycle_configuration" "tender" {
  bucket = aws_s3_bucket.tender.id

  rule {
    id     = "expire-failed-processing"
    status = "Enabled"
    filter {
      prefix = "failed/"
    }
    expiration {
      days = 90
    }
  }

  rule {
    id     = "transition-audit-to-ia"
    status = "Enabled"
    filter {
      prefix = "audit/"
    }
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    expiration {
      days = 365
    }
  }

  rule {
    id     = "expire-processing-artifacts"
    status = "Enabled"
    filter {
      prefix = "processing/"
    }
    expiration {
      days = 30
    }
  }
}

# -----------------------------------------------------------------------------
# Evidence Bucket — Mayzerock capability/compliance documents
# Also serves as S3 Vectors data source for Bedrock KB
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "evidence" {
  bucket        = "${var.project_name}-evidence-${var.environment}"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "evidence" {
  bucket                  = aws_s3_bucket.evidence.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "evidence_tls_only" {
  bucket = aws_s3_bucket.evidence.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.evidence.arn,
          "${aws_s3_bucket.evidence.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# S3 Event Notification — triggers Step Functions on tender upload (Phase 4+)
# -----------------------------------------------------------------------------
# resource "aws_s3_bucket_notification" "tender_upload" {
#   bucket = aws_s3_bucket.tender.id
#   ...
# }

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "tender_bucket_name" {
  value = aws_s3_bucket.tender.id
}

output "tender_bucket_arn" {
  value = aws_s3_bucket.tender.arn
}

output "evidence_bucket_name" {
  value = aws_s3_bucket.evidence.id
}

output "evidence_bucket_arn" {
  value = aws_s3_bucket.evidence.arn
}
