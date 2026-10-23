terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 5.0, < 7.0" }
  }
}

variable "bucket_name" { type = string }
data "aws_s3_bucket" "existing" { bucket = var.bucket_name }
output "bucket_arn" { value = data.aws_s3_bucket.existing.arn }
