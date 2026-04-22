# ════════════════════════════════════════════════════════════
# ecr.tf — Container Registries for voting app images
#
# Checkov rules satisfied:
#   ✅ CKV_AWS_51  — image tag immutability
#   ✅ CKV_AWS_136 — KMS encryption at rest
#   ✅ CKV_AWS_163 — scan on push enabled
# ════════════════════════════════════════════════════════════

locals {
  ecr_repos = ["vote", "result", "worker", "agent"]
}

resource "aws_ecr_repository" "app" {
  for_each = toset(local.ecr_repos)

  name                 = "${var.project_name}/${each.key}"
  image_tag_mutability = var.ecr_image_tag_mutability   # ✅ CKV_AWS_51

  # ✅ CKV_AWS_163 — scan on push
  image_scanning_configuration {
    scan_on_push = true
  }

  # ✅ CKV_AWS_136 — encryption at rest
  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = var.kms_key_arn != "" ? var.kms_key_arn : null
  }

  tags = {
    Name        = "${var.project_name}-${each.key}"
    Environment = var.environment
  }
}

# ── Lifecycle policy: keep last 10 images, remove untagged after 1 day
resource "aws_ecr_lifecycle_policy" "app" {
  for_each   = aws_ecr_repository.app
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Remove untagged images after 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Keep last 10 tagged images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = { type = "expire" }
      }
    ]
  })
}

# ── ECR repository policy — restrict to this account only ────
resource "aws_ecr_repository_policy" "app" {
  for_each   = aws_ecr_repository.app
  repository = each.value.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCurrentAccount"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
      }
    ]
  })
}
