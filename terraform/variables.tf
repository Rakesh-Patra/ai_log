# ════════════════════════════════════════════════════════════
# variables.tf — All configurable inputs
# Every variable has: description + type + validation
# No defaults for secrets — forces explicit values.
# ════════════════════════════════════════════════════════════

# ── Network & Access ──────────────────────────────────────

variable "admin_cidr" {
  description = "Your IP in CIDR notation for SSH/Vault/K8s access. Run: curl -s ifconfig.me && echo '/32'"
  type        = string

  validation {
    condition     = can(cidrhost(var.admin_cidr, 0))
    error_message = "admin_cidr must be a valid CIDR block (e.g. 203.0.113.10/32)."
  }
}

variable "vpc_id" {
  description = "VPC ID to deploy into. Leave empty for default VPC."
  type        = string
  default     = ""
}

variable "subnet_id" {
  description = "Subnet ID for EC2 instance. Leave empty for default subnet."
  type        = string
  default     = ""
}

variable "key_pair_name" {
  description = "AWS key pair name for SSH access. Create one in AWS Console → EC2 → Key Pairs."
  type        = string
  default     = ""
}

# ── Compute ───────────────────────────────────────────────

variable "instance_type" {
  description = "EC2 instance type. See free-tier logic below."
  type        = string
  default     = "m7i-flex.large"

  # ┌───────────────────────────────────────────────────────────────────┐
  # │ AWS Free Tier split:                                             │
  # │                                                                  │
  # │ Account created AFTER July 15, 2025:                             │
  # │   → m7i-flex.large is FREE via $200 credits (valid 6 months)     │
  # │   → 2 vCPU, 8 GB RAM — enough for K3s + Vault + AI Agent        │
  # │                                                                  │
  # │ Account created BEFORE July 15, 2025:                            │
  # │   → t2.micro/t3.micro: 1 vCPU, 1 GB ❌ too small for this stack │
  # │   → Use t3.small (~$15/mo) | 2 vCPU, 2 GB — minimum viable      │
  # └───────────────────────────────────────────────────────────────────┘

  validation {
    condition     = contains(["m7i-flex.large", "t3.small", "t3.medium"], var.instance_type)
    error_message = "Use m7i-flex.large (new-account free credits) or t3.small/t3.medium."
  }
}

variable "volume_size" {
  description = "Root EBS volume size in GB."
  type        = number
  default     = 20

  validation {
    condition     = var.volume_size >= 20 && var.volume_size <= 100
    error_message = "Volume size must be 20-100 GB."
  }
}

# ── Project Metadata ──────────────────────────────────────

variable "project" {
  description = "Project name used in resource naming and tags."
  type        = string
  default     = "k8s-voting-app"
}

variable "environment" {
  description = "Deployment environment. Affects resource naming and behavior."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "owner" {
  description = "Owner tag for cost tracking and resource identification."
  type        = string
  default     = "patracoder"
}

variable "aws_region" {
  description = "AWS region. ap-south-1 (Mumbai) for low latency from India."
  type        = string
  default     = "ap-south-1"
}

# ── Vault ─────────────────────────────────────────────────

variable "vault_address" {
  description = "URL of the HashiCorp Vault instance (e.g. http://<EC2_IP>:8200)"
  type        = string
  # No default — must be set via TF_VAR_vault_address or -var flag
}

variable "vault_aws_role" {
  description = "Vault AWS secrets engine role for issuing temporary credentials."
  type        = string
  default     = "terraform-role"
}

# ── ECR ───────────────────────────────────────────────────

variable "ecr_image_tag_mutability" {
  description = "ECR tag mutability. IMMUTABLE prevents tag overwrites (recommended)."
  type        = string
  default     = "IMMUTABLE"

  validation {
    condition     = contains(["MUTABLE", "IMMUTABLE"], var.ecr_image_tag_mutability)
    error_message = "Must be MUTABLE or IMMUTABLE."
  }
}

variable "kms_key_arn" {
  description = "KMS key ARN for encrypting ECR + S3. Empty = AWS-managed key (fine for dev)."
  type        = string
  default     = ""
}

# ── Naming (kept for backward compat) ─────────────────────

variable "project_name" {
  description = "Alias for project variable (backward compatibility)."
  type        = string
  default     = "k8s-voting-app"
}
