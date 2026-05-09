# WHY THIS EXISTS:
# AWS free credits ($200) expire in 6 months. Without a budget alert,
# you will not know when you transition from $0 to billed. A startup in 2019
# left a forgotten NAT Gateway running for 3 months and received a $47,000 bill.
# A Budget alarm is your circuit breaker.

resource "aws_budgets_budget" "monthly" {
  name         = "${var.project}-monthly-budget"
  budget_type  = "COST"
  limit_amount = "10"   # alert before credits expire
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80   # alert at 80% of $10
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.owner_email]
  }
}

resource "aws_budgets_budget" "credits_remaining" {
  name        = "${var.project}-credits-alert"
  budget_type = "CREDIT"
  # Alert when only $50 of $200 credits remain
  notification {
    comparison_operator        = "LESS_THAN"
    threshold                  = 50
    threshold_type             = "ABSOLUTE_VALUE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.owner_email]
  }
}
