# =============================================================================
# CloudWatch — Log groups + metric alarms
# =============================================================================

variable "project_name" { type = string }
variable "environment" { type = string }

locals {
  prefix = "${var.project_name}-${var.environment}"

  lambda_functions = [
    "intake",
    "document-profile",
    "textract",
    "ocr-quality",
    "normalize",
    "extract-requirements",
    "retrieve-evidence",
    "compliance",
    "risk-analysis",
    "bid-drafting",
    "output-validation",
    "persistence",
    "notification",
    "failure-handler"
  ]
}

# -----------------------------------------------------------------------------
# Log groups — one per Lambda, created ahead of function deployment
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "lambda" {
  for_each = toset(local.lambda_functions)

  name              = "/aws/lambda/${local.prefix}-${each.value}"
  retention_in_days = 90
}

resource "aws_cloudwatch_log_group" "step_functions" {
  name              = "/aws/states/${local.prefix}-workflow"
  retention_in_days = 90
}
