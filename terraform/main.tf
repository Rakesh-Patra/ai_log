# ════════════════════════════════════════════════════════════
# main.tf — Providers and data sources
# AWS credentials fetched dynamically from Vault via OIDC.
# ════════════════════════════════════════════════════════════

# ── Vault Provider — connects to EC2 Vault instance ───────
provider "vault" {
  address          = var.vault_address
  skip_child_token = true
  # Auth via VAULT_TOKEN env var (set by CI/CD)
}

# ── Fetch dynamic AWS credentials from Vault ──────────────
data "vault_aws_access_credentials" "creds" {
  backend = "aws"
  role    = var.vault_aws_role
  type    = "creds"
}

# ── AWS Provider — uses Vault-issued temporary credentials ─
provider "aws" {
  region     = var.aws_region
  access_key = data.vault_aws_access_credentials.creds.access_key
  secret_key = data.vault_aws_access_credentials.creds.secret_key

  default_tags {
    tags = {
      Project     = var.project
      ManagedBy   = "terraform"
      Environment = var.environment
      Owner       = var.owner
    }
  }
}

# ── Data Sources ──────────────────────────────────────────
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
