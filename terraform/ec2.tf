# ════════════════════════════════════════════════════════════
# ec2.tf — K3s + Vault Host
# Checkov compliant: CKV_AWS_8, CKV_AWS_25, CKV_AWS_79, CKV_AWS_88
# ════════════════════════════════════════════════════════════

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# ── Security Group ─────────────────────────────────────────
# WHY var.admin_cidr: 0.0.0.0/0 fails CKV_AWS_25 and is a real risk.
# Only your IP needs SSH/K8s API/Vault access.

resource "aws_security_group" "k3s" {
  name        = "${var.project}-${var.environment}-k3s-sg"
  description = "K3s + Vault host — restricted to admin CIDR"
  vpc_id      = var.vpc_id != "" ? var.vpc_id : null

  # SSH — restricted to admin only (prefer SSM Session Manager instead)
  ingress {
    description = "SSH from admin"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  # Kubernetes API — admin only
  ingress {
    description = "K8s API from admin"
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  # Vault UI/API — admin only
  ingress {
    description = "Vault from admin"
    from_port   = 8200
    to_port     = 8200
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  # HTTP — public (vote/result app)
  ingress {
    description = "HTTP public access"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS — public
  ingress {
    description = "HTTPS public access"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # NodePort range — admin only (Grafana:3000, vote:5000, result:5001 via NodePort)
  ingress {
    description = "NodePorts from admin"
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-k3s-sg"
  }
}

# ── EC2 Instance ───────────────────────────────────────────

resource "aws_instance" "k3s" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type # See variables.tf for free-tier logic

  key_name               = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.k3s.id]
  iam_instance_profile   = aws_iam_instance_profile.vault_ec2.name
  monitoring             = true # CKV_AWS_126: CloudWatch basic (free)

  # CKV_AWS_79: Enforce IMDSv2 (prevents SSRF-based credential theft)
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2 only
    http_put_response_hop_limit = 1
  }

  # CKV_AWS_8: Encrypted root volume
  root_block_device {
    volume_size = var.volume_size
    volume_type = "gp3"
    encrypted   = true # CKV_AWS_8
  }

  # WHY minimal user_data: Ansible handles K3s/Vault/Helm install (idempotent).
  # user_data only does the bare minimum to make the instance reachable.
  user_data = <<-EOF
    #!/bin/bash
    set -euo pipefail
    apt-get update -y
    apt-get install -y curl unzip jq

    # Install SSM Agent for secure console access (no SSH needed)
    snap install amazon-ssm-agent --classic
    systemctl enable --now snap.amazon-ssm-agent.amazon-ssm-agent.service

    echo "✅ Instance ready for Ansible provisioning"
  EOF

  tags = {
    Name        = "${var.project}-${var.environment}-k3s"
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "terraform"
    FreeCredits = var.instance_type == "m7i-flex.large" ? "true" : "false"
  }
}
