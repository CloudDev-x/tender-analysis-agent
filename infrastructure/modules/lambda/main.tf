resource "aws_lambda_layer_version" "mayzerock_shared" {
  filename            = "${path.module}/../../lambda-packages/lambda_layer_shared.zip"
  layer_name          = "${var.project_name}-shared-${var.environment}"
  compatible_runtimes = ["python3.11", "python3.12"]
  source_code_hash    = filebase64sha256("${path.module}/../../lambda-packages/lambda_layer_shared.zip")
}

locals {
  functions = {
    intake               = "intake"
    document_profile     = "document_profile"
    textract             = "textract"
    ocr_quality          = "ocr_quality"
    normalize            = "normalize"
    extract_requirements = "extract_requirements"
    retrieve_evidence    = "retrieve_evidence"
    compliance           = "compliance"
    risk_analysis        = "risk_analysis"
    bid_drafting         = "bid_drafting"
    output_validation    = "output_validation"
    persistence          = "persistence"
    notification         = "notification"
    failure_handler      = "failure_handler"
  }
}

resource "aws_lambda_function" "handlers" {
  for_each = local.functions

  filename      = "${path.module}/../../lambda-packages/lambda_${each.value}.zip"
  function_name = "${var.project_name}-${replace(each.key, "_", "-")}-${var.environment}"
  role          = var.lambda_roles[each.key]
  handler       = "${each.value}.lambda_handler"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = 256

  layers = [aws_lambda_layer_version.mayzerock_shared.arn]

  environment {
    variables = {
      ENVIRONMENT      = var.environment
      DYNAMODB_TABLE   = var.dynamodb_table_name
      KB_ID            = var.bedrock_kb_id
      BEDROCK_MODEL_ID = var.bedrock_model_id
      KMS_KEY_ID       = var.kms_key_id
    }
  }

  source_code_hash = filebase64sha256("${path.module}/../../lambda-packages/lambda_${each.value}.zip")

  depends_on = [aws_lambda_layer_version.mayzerock_shared]

  tags = {
    Name      = "${var.project_name}-${replace(each.key, "_", "-")}"
    Component = "tender-workflow"
  }
}

resource "aws_sfn_state_machine" "tender_workflow" {
  name       = "${var.project_name}-workflow-${var.environment}"
  role_arn   = var.step_functions_role_arn
  definition = templatefile("${path.module}/../../step-functions-state-machine.json", {
    AWS_REGION     = var.aws_region
    AWS_ACCOUNT_ID = var.aws_account_id
  })

  tags = {
    Name = "${var.project_name}-workflow"
  }

  depends_on = [aws_lambda_function.handlers]
}

output "lambda_function_arns" {
  value = { for k, v in aws_lambda_function.handlers : k => v.arn }
}

output "state_machine_arn" {
  value = aws_sfn_state_machine.tender_workflow.arn
}
