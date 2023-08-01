# Lambda 1: Ingestion
resource "aws_lambda_function" "s3_file_reader" {
  function_name = var.ingestion_lambda_name
  filename = data.archive_file.ingestion_lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  role = aws_iam_role.iam_for_lambda.arn
  handler = "src/postgres_data_capture.postgres_data_capture" # pythonfilename.functionname
  runtime = var.pythonversion
  timeout = 60
  layers = [aws_lambda_layer_version.lambda_layer.arn, "arn:aws:lambda:eu-west-2:336392948345:layer:AWSSDKPandas-Python310:3"]
  # depends_on = [ aws_cloudwatch_log_group.ingestion_lambda_log ]
}

# creates the log group for the lambda - done automatically through aws

# resource "aws_cloudwatch_log_group" "ingestion_lambda_log" {
#   name = "${var.ingestion_lambda_name}"
#   retention_in_days = 30

# }

# resource "aws_cloudwatch_log_stream" "ingestion_log_stream" {
#   name = "ingest-sql-totes"
#   log_group_name = aws_cloudwatch_log_group.ingestion_lambda_log.name
# }

resource "aws_lambda_layer_version" "lambda_layer" {
  filename   = "${path.module}/../layers/python.zip"
  layer_name = "psycopg2"
  compatible_runtimes = ["python3.10"]

# Lambda 1 Log Group: Creates the log group for the lambda
# resource "aws_cloudwatch_log_group" "ingestion_lambda_log" {
#   name = "aws/lambda/${var.ingestion_lambda_name}"
#   retention_in_days = 30
# }


# Lambda 2: Transformation
# update handler and sort out filename
resource "aws_lambda_function" "data_transform" {
  function_name = var.transformation_lambda_name
  filename = data.archive_file.transform_lambda.output_path
  source_code_hash = data.archive_file.transform_lambda.output_base64sha256
  role = aws_iam_role.iam_for_lambda.arn
  handler = "transform.lambda_handler" # pythonfilename.functionname
  runtime = var.pythonversion
#   depends_on = [ aws_cloudwatch_log_group.transform_lambda_log ]
}

# Lambda 2 Log Group: Creates the log group for the lambda
# resource "aws_cloudwatch_log_group" "transform_lambda_log" {
#   name = "aws/lambda/${var.transformation_lambda_name}"
#   retention_in_days = 30
# }

# Lambda 3: Data Loading 
resource "aws_lambda_function" "data_warehouse" {
  function_name = var.warehousing_lambda_name
  filename = data.archive_file.warehouse_lambda.output_path
  source_code_hash = data.archive_file.warehouse_lambda.output_base64sha256
  role = aws_iam_role.iam_for_lambda.arn
  handler = "warehouse.lambda_handler" # pythonfilename.functionname
  runtime = var.pythonversion
#   depends_on = [ aws_cloudwatch_log_group.warehouse_lambda_log ]
  }

# Lambda 3 Log Group: Creates the log group for the lambda
# resource "aws_cloudwatch_log_group" "warehouse_lambda_log" {
#   name = "aws/lambda/${var.warehousing_lambda_name}"
#   retention_in_days = 30
# }