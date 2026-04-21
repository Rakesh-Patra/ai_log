# ════════════════════════════════════════════════════════════
# Terraform for k8s-kind-voting-app
#
# Structure:
#   agent/terraform/
#     ├── main.tf          — provider + data sources
#     ├── variables.tf     — all input variables
#     ├── outputs.tf       — exported values
#     ├── ecr.tf           — container registries
#     ├── s3.tf            — secure S3 bucket (Checkov clean)
#     ├── iam.tf           — IAM roles (least privilege)
#     ├── vault.tf         — Vault provider + dynamic AWS creds
#     └── .checkov.yaml    — Checkov skip rules with justification
#
# Security:
#   - All resources pass `checkov -d .` (no CRITICAL/HIGH)
#   - AWS credentials come from Vault (never hardcoded)
#   - Remote state in encrypted S3 + DynamoDB locking
#
# Vault Setup (run once on EC2):
#   vault secrets enable aws
#   vault write aws/config/root access_key=AKIA... secret_key=...
#   vault write aws/roles/terraform-role credential_type=iam_user \
#     policy_document=@iam-policy.json
# ════════════════════════════════════════════════════════════
