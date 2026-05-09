# ════════════════════════════════════════════════════════════
# outputs.tf — Useful connection info after terraform apply
# ════════════════════════════════════════════════════════════

# ── Instance Access ───────────────────────────────────────

output "instance_public_ip" {
  description = "Public IP of the K3s host"
  value       = aws_instance.k3s.public_ip
}

output "instance_id" {
  description = "EC2 instance ID (needed for SSM)"
  value       = aws_instance.k3s.id
}

output "ssm_connect_command" {
  description = "Connect via SSM (no SSH key needed)"
  value       = "aws ssm start-session --target ${aws_instance.k3s.id}"
}

output "ssh_command" {
  description = "SSH command (if key pair was configured)"
  value       = var.key_pair_name != "" ? "ssh -i ${var.key_pair_name}.pem ubuntu@${aws_instance.k3s.public_ip}" : "No key pair configured — use SSM instead"
}

# ── Application URLs ──────────────────────────────────────

output "vault_ui_url" {
  description = "Vault Web UI"
  value       = "http://${aws_instance.k3s.public_ip}:8200/ui"
}

output "vote_app_url" {
  description = "Vote application URL"
  value       = "http://${aws_instance.k3s.public_ip}:5000"
}

output "result_app_url" {
  description = "Result application URL"
  value       = "http://${aws_instance.k3s.public_ip}:5001"
}

output "grafana_url" {
  description = "Grafana dashboard"
  value       = "http://${aws_instance.k3s.public_ip}:3000"
}

# ── Infrastructure Info ───────────────────────────────────

output "aws_account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
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
  description = "IAM role ARN for GitHub Actions OIDC"
  value       = aws_iam_role.github_actions.arn
}

# ── Cost Estimation ───────────────────────────────────────

output "monthly_cost" {
  description = "Estimated monthly cost"
  value       = var.instance_type == "m7i-flex.large" ? "$0 (AWS free credits, 6mo)" : "~$15/month"
}
