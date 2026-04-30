# ════════════════════════════════════════════════════════════
# main.tf — Providers, backend, and data sources
# AWS credentials are fetched dynamically from Vault.
# ════════════════════════════════════════════════════════════

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # ── Remote State: encrypted S3 + DynamoDB locking ──────────
  backend "s3" {
    bucket         = "k8s-voting-app-tfstate-0f0a738c"
    key            = "agent/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true # Checkov: CKV_AWS_119
    dynamodb_table = "k8s-voting-app-tfstate-lock"
    # kms_key_id     = "alias/terraform-state" # Optional: add if using custom KMS
  }
}

# ── Vault Provider — connects to your EC2 Vault instance ─────
provider "vault" {
  address = var.vault_address
  # Auth via token from env VAULT_TOKEN
}

# ── Fetch dynamic AWS credentials from Vault ─────────────────
data "vault_aws_access_credentials" "creds" {
  backend = "aws"
  role    = var.vault_aws_role
  type    = "creds"
}

# ── AWS Provider — uses Vault-issued temporary credentials ────
provider "aws" {
  region     = var.aws_region
  access_key = data.vault_aws_access_credentials.creds.access_key
  secret_key = data.vault_aws_access_credentials.creds.secret_key

  default_tags {
    tags = {
      Project     = "k8s-voting-app"
      ManagedBy   = "terraform"
      Environment = var.environment
      Owner       = "patracoder"
    }
  }
}

# ── Current AWS account info ──────────────────────────────────
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
