outputs "aws_account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
  sensitive   = false
}

output "ecr_repository_urls" {
  description = "ECR repository URLs for all app images"
  value       = { for k, v in aws_ecr_repository.app : k => v.repository_url }
}

output "artifacts_bucket_name" {
  description = "S3 bucket for build artifacts"
  value       = aws_s3_bucket.artifacts.bucket
}

output "tfstate_bucket_name" {
  description = "S3 bucket for Terraform state"
  value       = aws_s3_bucket.tfstate.bucket
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC (use in workflow)"
  value       = aws_iam_role.github_actions.arn
}

output "vault_ec2_instance_profile" {
  description = "IAM instance profile name for Vault EC2 instance"
  value       = aws_iam_instance_profile.vault_ec2.name
}
