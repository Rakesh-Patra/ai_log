# WHY THIS EXISTS:
# Centralise all cost-tracking tags in one place.
# Any resource that doesn't inherit these tags = untracked cost.
# When you have 200 resources across 5 teams and a surprise $40,000 AWS bill,
# the first question is: "which team owns this?" Without tags, you can't answer.

locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
    CostCenter  = "internship-project"
    FreeTier    = var.instance_type == "m7i-flex.large" ? "credits" : "paid"
  }
}
