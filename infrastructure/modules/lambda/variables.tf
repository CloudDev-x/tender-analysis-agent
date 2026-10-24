variable "environment" {
  description = "Environment name (prod)"
  type        = string
  validation {
    condition     = var.environment == "prod"
    error_message = "Only 'prod' environment is supported."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
}

variable "bedrock_kb_id" {
  description = "Bedrock Knowledge Base ID"
  type        = string
}

variable "bedrock_model_id" {
  description = "Bedrock model ID (Claude Haiku)"
  type        = string
  default     = "us.anthropic.claude-3-haiku-20240307-v1:0"
}

variable "lambda_roles" {
  description = "Map of Lambda function names to IAM role ARNs"
  type        = map(string)
}

variable "lambda_subnet_ids" {
  description = "Subnet IDs for Lambda VPC configuration"
  type        = list(string)
  default     = []
}

variable "lambda_security_group_ids" {
  description = "Security group IDs for Lambda VPC configuration"
  type        = list(string)
  default     = []
}

variable "step_functions_role_arn" {
  description = "IAM role ARN for Step Functions"
  type        = string
}

variable "textract_confidence" {
  description = "Textract confidence threshold (0.0-1.0)"
  type        = string
  default     = "0.80"
}

variable "ocr_confidence" {
  description = "OCR quality gate confidence threshold (0.0-1.0)"
  type        = string
  default     = "0.80"
}

variable "retrieval_score" {
  description = "Knowledge Base retrieval minimum score (0.0-1.0)"
  type        = string
  default     = "0.70"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
}
