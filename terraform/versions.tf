# ════════════════════════════════════════════════════════════
# versions.tf — Pin providers to prevent version drift
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

  # Backend configured via CI/CD environment variables:
  #   terraform init \
  #     -backend-config="bucket=k8s-voting-app-tfstate-0f0a738c" \
  #     -backend-config="key=terraform.tfstate" \
  #     -backend-config="region=ap-south-1"
  backend "s3" {}
}
