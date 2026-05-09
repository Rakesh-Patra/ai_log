# WHY THIS EXISTS:
# Manual unseal = 3am on-call nightmare.
# KMS auto-unseal: Vault seals on reboot, unseals itself in ~10 seconds.
# Every time your EC2 reboots, Vault seals itself. Without auto-unseal, ALL
# secret reads fail until someone manually runs `vault operator unseal`.

resource "aws_kms_key" "vault_unseal" {
  description             = "${var.project} vault auto-unseal"
  deletion_window_in_days = 10
  enable_key_rotation     = true
  tags                    = local.common_tags
}
