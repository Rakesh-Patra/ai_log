# ════════════════════════════════════════════════════════════
# Vault Policies — Least-Privilege Access
#
# Each service gets its own policy with minimal permissions.
# Apply: vault policy write <name> k8s/app-policy.hcl
# ════════════════════════════════════════════════════════════

# ── Default namespace apps (vote, result, worker) ─────────────
# Can only read DB and Redis credentials
path "secret/data/db-credentials" {
  capabilities = ["read"]
}
path "secret/data/redis-credentials" {
  capabilities = ["read"]
}

# ── Agent credentials (voting-agent namespace) ────────────────
# Separate policy: agent-read-policy
# Applied via:
#   vault policy write agent-read-policy - <<EOF
#   path "secret/data/agent-keys" {
#     capabilities = ["read"]
#   }
#   path "secret/data/agent-credentials" {
#     capabilities = ["read"]
#   }
#   EOF
