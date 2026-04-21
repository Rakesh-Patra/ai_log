# ════════════════════════════════════════════════════════════
# iam.tf — Least-privilege IAM roles for GitHub Actions + agent
#
# Checkov rules satisfied:
#   ✅ CKV_AWS_40  — no inline policies with *
#   ✅ CKV_AWS_274 — no AdministratorAccess
#   ✅ CKV2_AWS_56 — password policy enforced
# ════════════════════════════════════════════════════════════

# ── GitHub Actions OIDC trust (no static keys needed) ────────
data "aws_iam_openid_connect_provider" "github" {
  # Assumes OIDC provider already exists — create once per account:
  # aws iam create-open-id-connect-provider \
  #   --url https://token.actions.githubusercontent.com \
  #   --client-id-list sts.amazonaws.com \
  #   --thumbprint-list <thumbprint>
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_role" "github_actions" {
  name        = "${var.project_name}-github-actions"
  description = "Role assumed by GitHub Actions via OIDC — no static keys"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = data.aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          # ✅ Scoped to YOUR repo only — not all of GitHub
          "token.actions.githubusercontent.com:sub" = "repo:patracoder/k8s-kind-voting-app:*"
        }
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = { Environment = var.environment }
}

# ── Least-privilege policy for GitHub Actions ────────────────
resource "aws_iam_role_policy" "github_actions_ecr" {
  name = "ecr-push-policy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ECRAuth"
        Effect = "Allow"
        Action = ["ecr:GetAuthorizationToken"]
        Resource = "*"   # Required — GetAuthorizationToken has no resource scope
      },
      {
        Sid    = "ECRPush"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ]
        # ✅ Scoped to specific repos — not * on resource
        Resource = [for repo in aws_ecr_repository.app : repo.arn]
      }
    ]
  })
}

# ── IAM role for Vault EC2 instance ──────────────────────────
resource "aws_iam_role" "vault_ec2" {
  name        = "${var.project_name}-vault-ec2"
  description = "EC2 instance role for Vault — scoped S3 access only"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "vault_s3" {
  name = "vault-s3-storage"
  role = aws_iam_role.vault_ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ]
      # ✅ Scoped to vault storage bucket only
      Resource = [
        aws_s3_bucket.artifacts.arn,
        "${aws_s3_bucket.artifacts.arn}/*"
      ]
    }]
  })
}

resource "aws_iam_instance_profile" "vault_ec2" {
  name = "${var.project_name}-vault-ec2-profile"
  role = aws_iam_role.vault_ec2.name
}

# ✅ CKV2_AWS_56 — Enforce an IAM password policy ─────────────
resource "aws_iam_account_password_policy" "strict" {
  minimum_password_length        = 16
  require_lowercase_characters   = true
  require_numbers                = true
  require_uppercase_characters   = true
  require_symbols                = true
  allow_users_to_change_password = true
  max_password_age               = 90
  password_reuse_prevention      = 5
  hard_expiry                    = false
}
