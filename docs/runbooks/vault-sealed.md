# WHY THIS EXISTS:
# A sealed Vault takes down the entire platform since pods can't pull secrets.

## Symptom
Grafana alert: VaultSealed fires. All services show secret read errors.

## Why this happens
Vault seals itself after a reboot as a security measure.
If KMS auto-unseal is not configured, it requires 3 manual unseal keys.

## Fix (with KMS auto-unseal configured — Phase 2C)
Vault unseals automatically. Verify with:
  `curl http://<vault-addr>:8200/v1/sys/health`

## Fix (without KMS — emergency procedure)
  `vault operator unseal <key1>`
  `vault operator unseal <key2>`
  `vault operator unseal <key3>`
  # Keys were generated during vault operator init — stored WHERE?
  # This is why you must document key storage location in SECURITY.md

## Prevention
Implement `kms.tf` from Phase 2C
