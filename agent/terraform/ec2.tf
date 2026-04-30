# ════════════════════════════════════════════════════════════
# ec2.tf — Provision K3s & Vault Host
# ════════════════════════════════════════════════════════════

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_security_group" "k3s_host" {
  name        = "k3s-vault-host-sg"
  description = "Security group for K3s and Vault host"

  # SSH access (Restrict this to your IP in production!)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Kubernetes API
  ingress {
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Vault UI / API
  ingress {
    from_port   = 8200
    to_port     = 8200
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP / Web Traffic (Vote/Result App)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "k3s-vault-host-sg"
  }
}

resource "aws_instance" "k3s_host" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "m7i-flex.large" # Requested by User

  # Ensure you associate a key pair here if you want to SSH into the box:
  # key_name = "your-aws-key-name"

  vpc_security_group_ids = [aws_security_group.k3s_host.id]
  iam_instance_profile   = aws_iam_instance_profile.vault_ec2.name

  root_block_device {
    volume_size = 40 # 40GB SSD
    volume_type = "gp3"
  }

  # This user-data script installs K3s automatically on boot
  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y curl unzip
              
              # Install K3s
              curl -sfL https://get.k3s.io | sh -
              
              # Give default ubuntu user access to kubectl
              mkdir -p /home/ubuntu/.kube
              cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
              chown ubuntu:ubuntu /home/ubuntu/.kube/config
              chmod 600 /home/ubuntu/.kube/config

              # Export kubeconfig path
              echo "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml" >> /etc/profile
              EOF

  tags = {
    Name = "K3s-Vault-Host"
  }
}

output "k3s_host_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.k3s_host.public_ip
}
