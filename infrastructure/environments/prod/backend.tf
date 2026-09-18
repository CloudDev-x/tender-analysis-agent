# =============================================================================
# Remote State Backend — Prod Environment
# =============================================================================
# Prerequisites: run scripts/bootstrap-state.sh before terraform init.
# =============================================================================

terraform {
  backend "s3" {
    bucket         = "mayzerock-terraform-state-prod"
    key            = "tender-system/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "mayzerock-terraform-locks-prod"
    encrypt        = true
  }
}
