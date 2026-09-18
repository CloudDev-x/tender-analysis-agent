# =============================================================================
# AWS Budgets — Monthly cost alerts
# =============================================================================

variable "project_name" { type = string }
variable "budget_limit" { type = number }
variable "alert_thresholds" { type = list(number) }
variable "alert_emails" {
  type      = list(string)
  sensitive = true
}

resource "aws_budgets_budget" "monthly" {
  name         = "${var.project_name}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_limit)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "TagKeyValue"
    values = ["user:Project$${var.project_name}"]
  }

  dynamic "notification" {
    for_each = var.alert_thresholds
    content {
      comparison_operator       = "GREATER_THAN"
      threshold                 = (notification.value / var.budget_limit) * 100
      threshold_type            = "PERCENTAGE"
      notification_type         = "ACTUAL"
      subscriber_email_addresses = var.alert_emails
    }
  }
}
