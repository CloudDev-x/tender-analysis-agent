# =============================================================================
# Production Environment — Variable Declarations
# =============================================================================

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"

  validation {
    condition     = var.environment == "prod"
    error_message = "This configuration is production-only."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used in resource naming"
  type        = string
  default     = "mayzerock-tender"
}

variable "bedrock_inference_model_id" {
  description = "Bedrock model ID for generative inference (US Geo inference profile)"
  type        = string
  default     = "us.anthropic.claude-3-haiku-20240307-v1:0"
}

variable "bedrock_embedding_model_arn" {
  description = "ARN of the embedding model for Knowledge Base vectorization"
  type        = string
  default     = "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
}

variable "budget_limit" {
  description = "Monthly budget ceiling in USD"
  type        = number
  default     = 450
}

variable "budget_alert_thresholds" {
  description = "Budget alert thresholds in USD"
  type        = list(number)
  default     = [150, 200, 250, 300, 375, 450]
}

variable "budget_alert_emails" {
  description = "Email addresses for budget alerts"
  type        = list(string)
  sensitive   = true
}

variable "ses_sender_email" {
  description = "Verified SES sender email address"
  type        = string
}

variable "ses_recipient_emails" {
  description = "Bid team email addresses for tender notifications"
  type        = list(string)
  sensitive   = true
}

variable "estimated_tenders_per_month" {
  description = "Reference workload: expected tenders per month"
  type        = number
  default     = 50
}

variable "estimated_pages_per_tender" {
  description = "Reference workload: expected pages per tender"
  type        = number
  default     = 60
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default     = {}
}

variable "bedrock_kb_id" {
  description = "Bedrock Knowledge Base ID (set after KB creation)"
  type        = string
  default     = "QTOPS4AKNZ"
}
