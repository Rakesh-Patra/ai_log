# ════════════════════════════════════════════════════════════
# variables.tf — All configurable inputs
# No defaults for secrets — forces explicit values.
# ════════════════════════════════════════════════════════════

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev / staging / prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "vault_address" {
  description = "URL of the HashiCorp Vault instance (e.g. http://<EC2_IP>:8200)"
  type        = string
  # No default — must be set via TF_VAR_vault_address or tfvars
}

variable "vault_aws_role" {
  description = "Vault AWS secrets engine role name for issuing temporary credentials"
  type        = string
  default     = "terraform-role"
}

variable "project_name" {
  description = "Project identifier used in resource naming"
  type        = string
  default     = "k8s-voting-app"
}

variable "ecr_image_tag_mutability" {
  description = "ECR image tag mutability (IMMUTABLE recommended for prod)"
  type        = string
  default     = "IMMUTABLE"   # Checkov: CKV_AWS_51
  validation {
    condition     = contains(["MUTABLE", "IMMUTABLE"], var.ecr_image_tag_mutability)
    error_message = "Must be MUTABLE or IMMUTABLE."
  }
}

variable "kms_key_arn" {
  description = "ARN of the KMS key used for encrypting ECR + S3"
  type        = string
  default     = ""   # If empty, uses AWS-managed key (acceptable for dev)
}
