# =============================================================================
# Dev Environment — Outputs
# =============================================================================

output "tender_bucket_name" {
  description = "S3 bucket for tender documents and processing"
  value       = module.s3.tender_bucket_name
}

output "evidence_bucket_name" {
  description = "S3 bucket for Mayzerock evidence documents"
  value       = module.s3.evidence_bucket_name
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.dynamodb.table_name
}

output "kms_key_arn" {
  description = "KMS key ARN"
  value       = module.kms.key_arn
}
