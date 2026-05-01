# ════════════════════════════════════════════════════════════
# vault.tf — HashiCorp Vault configuration via Terraform
#
# This file configures the Vault secrets engine and GitHub
# Actions OIDC JWT auth.
#
# Vault must already be running on EC2.
# Run once: terraform apply -target=vault_aws_secret_backend.aws
# ════════════════════════════════════════════════════════════

# ── Enable the AWS secrets engine ────────────────────────────
resource "vault_aws_secret_backend" "aws" {
  path        = "aws"
  description = "AWS secrets engine for dynamic IAM credentials"

  # These come from environment: VAULT_AWS_ACCESS_KEY_ID / SECRET
  # Never hardcode credentials here.
  default_lease_ttl_seconds = 3600 # 1 hour max
  max_lease_ttl_seconds     = 3600
}

# ── Vault role: Terraform CI/CD (S3 + ECR access) ────────────
resource "vault_aws_secret_backend_role" "terraform_role" {
  backend         = vault_aws_secret_backend.aws.path
  name            = "terraform-role"
  credential_type = "iam_user"

  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:*",
          "ec2:*",
          "s3:Get*",
          "s3:List*",
          "s3:PutObject",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:Describe*",
          "dynamodb:List*",
          "iam:Get*",
          "iam:List*"
        ]
        Resource = [
          "arn:aws:ecr:*:*:repository/ai-log/*",
          "arn:aws:s3:::ai-log-artifacts-*",
          "arn:aws:s3:::k8s-voting-app-tfstate-*",
          "arn:aws:s3:::k8s-voting-app-access-logs-*",
          "arn:aws:dynamodb:*:*:table/k8s-voting-app-tfstate-lock",
          "*"
        ]
      }
    ]
  })
}

# ── Enable JWT auth (for GitHub Actions OIDC) ────────────────
resource "vault_jwt_auth_backend" "github_actions" {
  path               = "jwt"
  type               = "jwt"
  oidc_discovery_url = "https://token.actions.githubusercontent.com"
  bound_issuer       = "https://token.actions.githubusercontent.com"
  description        = "GitHub Actions OIDC auth"
}

# ── Vault policy: allow reading terraform-role creds ─────────
resource "vault_policy" "terraform_ci" {
  name = "terraform-ci-policy"

  policy = <<-EOT
    path "aws/creds/terraform-role" {
      capabilities = ["read"]
    }
    path "secret/data/*" {
      capabilities = ["read", "create", "update", "delete"]
    }
    path "sys/mounts/*" {
      capabilities = ["read", "list", "create", "update", "delete"]
    }
    path "sys/auth/*" {
      capabilities = ["read", "list", "create", "update", "delete"]
    }
    path "sys/policies/acl/*" {
      capabilities = ["read", "list", "create", "update", "delete"]
    }
    path "aws/*" {
      capabilities = ["create", "read", "update", "delete", "list"]
    }
    path "auth/jwt/*" {
      capabilities = ["create", "read", "update", "delete", "list"]
    }
  EOT
}

# ── JWT role: binds GitHub repo → Vault policy ───────────────
resource "vault_jwt_auth_backend_role" "github_actions" {
  backend        = vault_jwt_auth_backend.github_actions.path
  role_name      = "gh-actions-role"
  token_policies = [vault_policy.terraform_ci.name]
  token_ttl      = 3600

  bound_audiences = ["https://github.com/Rakesh-Patra"]
  user_claim      = "sub"
  role_type       = "jwt"

  bound_claims_type = "glob"
  bound_claims = {
    # ✅ Scoped to this repo only
    sub = "repo:Rakesh-Patra/ai_log:*"
  }
}

# ── Enable KV v2 secrets engine ──────────────────────────────
resource "vault_mount" "kv" {
  path    = "secret"
  type    = "kv"
  options = { version = "2" }
}

# ── Seed initial secret paths (values set out-of-band) ───────
# These create the PATH only — not the actual secret values.
# Run manually: vault kv put secret/db-credentials username=admin password=...
resource "vault_kv_secret_v2" "db_credentials_placeholder" {
  mount               = vault_mount.kv.path
  name                = "db-credentials"
  delete_all_versions = false

  data_json = jsonencode({
    # ⚠️ PLACEHOLDER — override immediately after apply:
    #   vault kv put secret/db-credentials username=admin password=...
    host = "db.default.svc.cluster.local"
  })

  lifecycle {
    ignore_changes = [data_json] # Don't overwrite manual updates
  }
}

# Trigger Push: State Reconciliation Complete
