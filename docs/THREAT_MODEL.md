# STRIDE Threat Model — k8s-kind-voting-app
# Day 1: DevSecOps Mindset & Threat Modeling
#
# Framework: STRIDE
#   S — Spoofing        (impersonating users/services)
#   T — Tampering       (modifying data or code)
#   R — Repudiation     (denying actions occurred)
#   I — Information Disclosure (exposing sensitive data)
#   D — Denial of Service (making system unavailable)
#   E — Elevation of Privilege (gaining unauthorized access)
# ════════════════════════════════════════════════════════════

## System Overview

### Architecture (3-tier)
```
[Browser]
    │ HTTP
    ▼
[vote (Python/Flask, port 80)]   [result (Node.js, port 80)]
    │ Redis                             │ PostgreSQL
    ▼                                  ▼
[redis (port 6379)] ←── [worker (.NET)] ──→ [postgres (port 5432)]
                                            ▲
                                   [agent (FastAPI, port 8000)]
                                            │ K8s API / Prometheus
```

### Trust Boundaries
1. **External → vote/result**: internet-facing ingress
2. **vote → redis**: internal backend
3. **worker → redis + postgres**: internal data pipeline
4. **result → postgres**: internal read path
5. **agent → K8s API**: privileged cluster access
6. **CI/CD → Vault → AWS**: infrastructure provisioning path

---

## STRIDE Analysis

### S — Spoofing

| Threat | Component | Mitigation | Status |
|---|---|---|---|
| Attacker impersonates a pod to read secrets | All pods | Per-component ServiceAccounts + `automountServiceAccountToken: false` | ✅ Done |
| Rogue CI job impersonates GitHub Actions to get AWS creds | GitHub Actions → Vault | OIDC JWT with `bound_claims` scoped to `repo:patracoder/k8s-kind-voting-app:*` | ✅ Done |
| Attacker calls K8s API as agent ServiceAccount | agent → K8s API | ClusterRole is read-only (get/list/watch only) | ✅ Done |
| Spoofed Docker image (wrong digest) | ECR | Image signature verification (Kyverno + Cosign) | ✅ Done |
| **OPEN** — No mTLS between services | vote↔redis, worker↔postgres | Consider Istio/Linkerd service mesh | ⚠️ Gap |

### T — Tampering

| Threat | Component | Mitigation | Status |
|---|---|---|---|
| Attacker modifies Terraform before apply | Terraform CI | Checkov scan blocks non-compliant code | ✅ Done |
| Malicious commit pushes secrets to main | Git | Gitleaks pre-commit + GitHub Actions scan | ✅ Done |
| Container image tampered between build and deploy | Docker → ECR | Trivy scan + Cosign signing + Kyverno verification | ✅ Done |
| Pod writes to filesystem and persists malware | All pods | `readOnlyRootFilesystem: true` in all deployments | ✅ Done |
| K8s manifest deployed without security review | k8s/ | CODEOWNERS requires @patracoder review | ✅ Done |

### R — Repudiation

| Threat | Component | Mitigation | Status |
|---|---|---|---|
| No audit trail for kubectl commands | K8s API | K8s API Audit Logging enabled to `/var/log/kubernetes/audit.log` | ✅ Done |
| CI/CD deploy with no trace of who approved | GitHub Actions | PR required + CODEOWNERS mandatory review | ✅ Done |
| Vault secret access not logged | Vault | Vault audit log path configured | ✅ Done |
| Agent tool calls not audited | AI Agent | LangSmith tracing enabled | ✅ Done |

### I — Information Disclosure

| Threat | Component | Mitigation | Status |
|---|---|---|---|
| DB password exposed in environment variables | worker, result | Vault agent-inject or ESO secretRef (not plaintext) | ✅ Done |
| Secrets committed to Git | All | Gitleaks + hardened .gitignore | ✅ Done |
| Kubernetes Secret readable by any pod | K8s Secrets | RBAC: `resourceNames` scoped to specific secrets | ✅ Done |
| Container image leaks source code or .env | Docker | .dockerignore blocks .env, venv, tests, secrets | ✅ Done |
| Prometheus exposes all metrics globally | Prometheus | NetworkPolicy limits egress to 9090 | ✅ Done |
| K8s Secrets stored base64 (plaintext) in etcd | etcd | **etcd Encryption at Rest** (AES-CBC) enabled | ✅ Done |

### D — Denial of Service

| Threat | Component | Mitigation | Status |
|---|---|---|---|
| Pod consumes all CPU/RAM on node | All pods | Resource requests + limits on every container | ✅ Done |
| Container forks bomb | All pods | `pidsLimit` set in K8s (baseline/restricted PSA) | ✅ Done |
| Redis flooded by rogue pod | redis | NetworkPolicy allows only vote + worker | ✅ Done |
| High load breaks single pod instances | App | **HPA (Horizontal Pod Autoscaler)** scaling pods automatically | ✅ Done |
| Service unavailable during upgrades | App | **PDB (PodDisruptionBudget)** ensuring minAvailable=1 | ✅ Done |

### E — Elevation of Privilege

| Threat | Component | Mitigation | Status |
|---|---|---|---|
| Container runs as root | All containers | `runAsNonRoot: true` + **PSA (restricted)** enforced | ✅ Done |
| Container breaks out via privileged mode | All containers | `privileged: false` + Kyverno enforcement | ✅ Done |
| Container gains more privileges via setuid | All containers | `allowPrivilegeEscalation: false` | ✅ Done |
| Linux capability abuse | All containers | `capabilities: drop: [ALL]` | ✅ Done |
| Kyverno policy bypassed | System | PSA labels on all namespaces | ✅ Done |

---

## Post-Hardening Priority List

| Priority | Item | Resolution |
|---|---|---|
| ✅ CLOSED | Image signing (Cosign) | Added sign/verify in CI and Kyverno |
| ✅ CLOSED | etcd not encrypted at rest | Added EncryptionConfiguration |
| ✅ CLOSED | Pod Security Admission | Labeled namespaces with restricted status |
| ✅ CLOSED | K8s API audit logging | Added audit policy and kind config |
| ✅ CLOSED | HPA/PodDisruptionBudget | Added manifests in `k8s/hpa-pdb.yaml` |
| 🟡 MED | No mTLS between services | Recommended for Phase 2 (Service Mesh) |


---

## Shift Left Summary

```
Code Commit
  └─ Gitleaks (pre-commit)          ← Shift Left: developer's machine
       └─ Gitleaks (CI)             ← Shift Left: before merge
            └─ Checkov (Terraform)  ← Shift Left: before infra apply
                 └─ Hadolint        ← Shift Left: before image built
                      └─ Trivy      ← before image pushed
                           └─ Kyverno ← before pod scheduled in K8s
                                └─ NetworkPolicy ← runtime zero-trust
```

**Security cost is cheapest at the LEFT. Most expensive at the RIGHT.**
