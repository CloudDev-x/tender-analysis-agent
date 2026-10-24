#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_ROOT}/build/lambda"
OUTPUT_DIR="${PROJECT_ROOT}/infrastructure/lambda-packages"

echo "Building Lambda packages for Mayzerock Tender System..."
mkdir -p "$BUILD_DIR"
mkdir -p "$OUTPUT_DIR"

# Build Lambda Layer (shared code)
echo "Building Lambda Layer (shared code)..."
LAYER_DIR="${BUILD_DIR}/python"
mkdir -p "$LAYER_DIR/lib/python3.11/site-packages"

# Copy src directory to layer
cp -r "${PROJECT_ROOT}/src" "$LAYER_DIR/lib/python3.11/site-packages/"

# Install layer dependencies (manually specify)
python -m pip install \
  boto3 \
  botocore \
  pydantic \
  pydantic-settings \
  python-json-logger \
  -t "$LAYER_DIR/lib/python3.11/site-packages/" --quiet

# Package layer
cd "$LAYER_DIR"
zip -r -q "${OUTPUT_DIR}/lambda_layer_shared.zip" .
cd "$PROJECT_ROOT"

echo "✓ Lambda Layer built: ${OUTPUT_DIR}/lambda_layer_shared.zip"

# Define handler functions
HANDLERS=(
    "intake"
    "document_profile"
    "textract"
    "ocr_quality"
    "normalize"
    "extract_requirements"
    "retrieve_evidence"
    "compliance"
    "risk_analysis"
    "bid_drafting"
    "output_validation"
    "persistence"
    "notification"
    "failure_handler"
)

# Build .zip for each handler
for handler in "${HANDLERS[@]}"; do
    echo "Building lambda_${handler}.zip..."
    
    HANDLER_DIR="${BUILD_DIR}/handler_${handler}"
    mkdir -p "$HANDLER_DIR"
    
    # Copy handler file
    cp "${PROJECT_ROOT}/src/handlers/${handler}.py" "$HANDLER_DIR/"
    
    # Copy config and models
    cp -r "${PROJECT_ROOT}/src/config" "$HANDLER_DIR/src/config"
    cp -r "${PROJECT_ROOT}/src/models" "$HANDLER_DIR/src/models"
    cp -r "${PROJECT_ROOT}/src/repositories" "$HANDLER_DIR/src/repositories"
    cp -r "${PROJECT_ROOT}/src/services" "$HANDLER_DIR/src/services"
    cp -r "${PROJECT_ROOT}/src/prompts" "$HANDLER_DIR/src/prompts"
    cp "${PROJECT_ROOT}/src/__init__.py" "$HANDLER_DIR/src/"
    
    # Create __init__.py files
    touch "$HANDLER_DIR/src/handlers/__init__.py"
    
    # Package into .zip
    cd "$HANDLER_DIR"
    zip -r -q "${OUTPUT_DIR}/lambda_${handler}.zip" .
    cd "$PROJECT_ROOT"
    
    echo "✓ lambda_${handler}.zip built"
done

echo ""
echo "All Lambda packages built successfully:"
ls -lh "$OUTPUT_DIR"/lambda_*.zip

echo ""
echo "Next steps:"
echo "1. Update infrastructure/environments/prod/terraform.tfvars with bedrock_kb_id"
echo "2. Run: cd infrastructure/environments/prod && terraform apply"
echo ""
