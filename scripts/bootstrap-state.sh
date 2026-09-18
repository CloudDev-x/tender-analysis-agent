#!/usr/bin/env bash
# =============================================================================
# Bootstrap Terraform Remote State — Production Only
# =============================================================================
# Run ONCE before terraform init.
# Creates: S3 bucket (state) + DynamoDB table (locking)
#
# Usage:
#   ./scripts/bootstrap-state.sh
# =============================================================================

set -euo pipefail

REGION="${AWS_DEFAULT_REGION:-us-east-1}"
BUCKET="mayzerock-terraform-state-prod"
TABLE="mayzerock-terraform-locks-prod"

echo "==> Creating state bucket: ${BUCKET}"
if [ "${REGION}" = "us-east-1" ]; then
  aws s3api create-bucket \
    --bucket "${BUCKET}" \
    --region "${REGION}" \
    2>/dev/null || echo "    Bucket already exists"
else
  aws s3api create-bucket \
    --bucket "${BUCKET}" \
    --region "${REGION}" \
    --create-bucket-configuration LocationConstraint="${REGION}" \
    2>/dev/null || echo "    Bucket already exists"
fi

echo "==> Enabling versioning"
aws s3api put-bucket-versioning \
  --bucket "${BUCKET}" \
  --versioning-configuration Status=Enabled

echo "==> Enabling encryption"
aws s3api put-bucket-encryption \
  --bucket "${BUCKET}" \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }'

echo "==> Blocking public access"
aws s3api put-public-access-block \
  --bucket "${BUCKET}" \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

echo "==> Creating lock table: ${TABLE}"
aws dynamodb create-table \
  --table-name "${TABLE}" \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "${REGION}" \
  2>/dev/null || echo "    Table already exists"

echo "==> Done. Run: cd infrastructure/environments/prod && terraform init"
