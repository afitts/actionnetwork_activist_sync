provider "aws" {
  access_key                  = "mock_access_key"
  secret_key                  = "mock_secret_key"
  region                      = "us-east-1"
  s3_force_path_style         = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  skip_get_ec2_platforms      = true


  endpoints {
    # apigateway     = "http://localhost:4567"
    # cloudformation = "http://localhost:4581"
    # cloudwatch     = "http://localhost:4582"
    dynamodb       = "http://localhost:4569"
    # es             = "http://localhost:4578"
    # firehose       = "http://localhost:4573"
    # iam            = "http://localhost:4593"
    # kinesis        = "http://localhost:4568"
    # lambda         = "http://localhost:4574"
    # route53        = "http://localhost:4580"
    # redshift       = "http://localhost:4577"
    s3             = "http://localhost:4566"
    # secretsmanager = "http://localhost:4584"
    # ses            = "http://localhost:4579"
    # sns            = "http://localhost:4575"
    sqs            = "http://localhost:4576"
    # ssm            = "http://localhost:4583"
    # stepfunctions  = "http://localhost:4585"
    # sts            = "http://localhost:4592"
  }
}

resource "aws_s3_bucket" "an-sync-bucket" {
  bucket = format("%s.%s", var.bucket, var.domain)
  acl    = "public-read-write"
}

resource "aws_sqs_queue" "an-sync-ingested" {
  name = "an-sync-ingested"
}

