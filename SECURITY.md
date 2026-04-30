## Security (Read before publishing)

This repository is designed to be **safe to publish** (no secrets committed) and **safe-by-default** (no "copy/paste root token" manifests).

It cannot guarantee **zero risk** once deployed publicly. You must still operate it securely.

### Publishing checklist (do this before GitHub)

- **Verify no real secrets are tracked**
  - Do not commit: Vault root tokens, unseal keys, API keys, kubeconfigs, TLS private keys, `.env` files.
  - Run a secret scan (example): `gitleaks detect --no-git`

- **Kubeconfig hygiene**
  - Never publish kubeconfigs (they often contain client certs/keys).
  - Keep generated kubeconfigs in a gitignored path (e.g. `kubeconfig_agent/`).

- **Vault hygiene**
  - Never publish `vault-init.json` or any init output.
  - Do not use the Vault **root token** for applications or External Secrets.
  - Prefer **Vault Kubernetes auth** for External Secrets Operator (ESO). Token auth is acceptable only for demos with a **scoped, short-lived token**.

- **Service exposure**
  - Do not expose the AI agent directly as a public `LoadBalancer`.
  - Put public entrypoints behind an Ingress/Gateway with **TLS + authentication**.

### Production requirements (minimum bar)

- **TLS everywhere**
  - Vault over HTTPS (no `tls_disable=1`)
  - Public traffic only over HTTPS (cert-manager recommended)

- **Least privilege**
  - Agent RBAC should be read-only unless you explicitly need mutations.
  - Avoid granting access to `secrets` unless strictly required.

- **Network controls**
  - Default-deny NetworkPolicies and explicit egress allow-lists.
  - Restrict Vault ingress to only ESO / injector / required workloads.

### If a secret was ever exposed

Assume compromise and rotate immediately:
- Vault root token / unseal keys
- Any Kubernetes credentials (kubeconfigs, SA tokens)
- API keys (Gemini/LangSmith/etc.)
