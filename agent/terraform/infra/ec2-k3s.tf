# ════════════════════════════════════════════════════════════
# ec2-k3s.tf — Minimal Cost Kubernetes Node
# ════════════════════════════════════════════════════════════

# ── IAM Role for AWS Systems Manager (Secure Shell Access) ────
resource "aws_iam_role" "k3s_node_role" {
  name = "${var.project_name}-k3s-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

# Attach SSM policy so we can securely access the node without opening port 22
resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.k3s_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "k3s_profile" {
  name = "${var.project_name}-k3s-profile"
  role = aws_iam_role.k3s_node_role.name
}

# ── EC2 Instance (K3s Server) ─────────────────────────────────
# Get latest Ubuntu 22.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "k3s" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "m7i-flex.large" # Free tier eligible as per user screenshot

  subnet_id                   = aws_subnet.public[0].id
  vpc_security_group_ids      = [aws_security_group.k3s_node.id]
  iam_instance_profile        = aws_iam_instance_profile.k3s_profile.name
  associate_public_ip_address = true

  root_block_device {
    volume_size = 20 # 20 GB Storage
    volume_type = "gp2"
  }

  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Update OS and install prerequisites
    apt-get update
    apt-get install -y curl jq

    # Install K3s (Server Node)
    # We add --tls-san so the remote kubeconfig can use the public IP
    export INSTALL_K3S_EXEC="--tls-san $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
    curl -sfL https://get.k3s.io | sh -

    # Wait for K3s to be ready
    sleep 15

    # Make kubeconfig readable by ubuntu user
    cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kubeconfig
    chown ubuntu:ubuntu /home/ubuntu/.kubeconfig

    # Rewrite the local IP in the kubeconfig to the public IP so we can download it
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    sed -i "s/127.0.0.1/$PUBLIC_IP/g" /home/ubuntu/.kubeconfig
  EOF

  tags = {
    Name = "${var.project_name}-k3s-node"
  }
}
