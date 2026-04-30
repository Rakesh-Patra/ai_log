# ════════════════════════════════════════════════════════════
# variables.tf — Minimal Cost Infrastructure
# ════════════════════════════════════════════════════════════

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project identifier used in resource naming"
  type        = string
  default     = "k8s-voting-app"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}
