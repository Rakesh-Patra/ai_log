# Kubernetes Voting App — Production-Grade DevSecOps on Kind

End-to-end **multi-service voting application** (Vote → Redis → Worker → Postgres → Result) deployed on **Kubernetes (kind)**, hardened with a **5-day DevSecOps curriculum** covering threat modeling, Git security, IaC scanning, container hardening, and Kubernetes zero-trust. An optional **AI SRE Agent** (`agent/`) provides autonomous cluster observability using LangGraph, Gemini, and MCP tooling.

## What's in this repo

| Area | Description | Images (Docker Hub) |
|------|-------------|---------------------|
| **Microservices** | `vote/` (Python), `worker/` (.NET), `result/` (Node.js) | `patracoder/examplevotingapp_vote:v1.0`<br>`patracoder/examplevotingapp_result:v1.0`<br>`patracoder/examplevotingapp_worker:v1.0` |
| **Kubernetes** | `k8s/` — hardened manifests, kind-oriented setup | — |
| **Platform** | kind, kubectl, Gateway API, Envoy, Argo CD | — |
| **Secret Management** | HashiCorp Vault + External Secrets Operator (ESO) | — |
| **AI SRE Agent** | `agent/` — FastAPI, MCP, LangGraph, Guardrails AI | `patracoder/k8s-ai-agent:v1.0` |

## Architecture

![Architecture diagram](k8s-kind-voting-app.png)

```
┌──────────┐     ┌───────┐     ┌────────┐     ┌──────────┐     ┌────────┐
│  Vote UI │────▸│ Redis │────▸│ Worker │────▸│ Postgres │◂────│ Result │
│ (Python) │     │       │     │ (.NET) │     │          │     │(Node)  │
└──────────┘     └───────┘     └────────┘     └──────────┘     └────────┘
       ▲                                            ▲
       │              ┌──────────────┐              │
       └──────────────│  Vault (ESO) │──────────────┘
                      │ Secret Sync  │
                      └──────────────┘
```

## Secret Management (Vault + External Secrets Operator)

Secrets are **never hardcoded** in manifests or committed to Git. The architecture follows a production-grade pattern:

1. **Vault** (Source of Truth) — Stores all DB and Redis credentials at `secret/data/db-credentials` and `secret/data/redis-credentials`.
2. **External Secrets Operator** — Syncs Vault secrets into native Kubernetes `Secret` objects (`db-secret`, `redis-secret`) every hour.
3. **Pods** — Consume credentials via standard `envFrom: secretRef`, requiring zero application-level Vault code.

Key files:
- `k8s/external-secrets.yaml` — `SecretStore` + `ExternalSecret` CRDs
- `k8s/app-policy.hcl` — Vault read-only policy for the app role

## DevSecOps — 5-Day Implementation

> Full status tracker: [`DEVSECOPS_STATUS.md`](DEVSECOPS_STATUS.md)

| Day | Focus | Key Deliverables |
|-----|-------|------------------|
| **1** | Threat Modeling | STRIDE analysis, [`THREAT_MODEL.md`](THREAT_MODEL.md) |
| **2** | Git Security | Gitleaks, pre-commit hooks, Dependabot, CODEOWNERS |
| **3** | IaC Security | Checkov CI, Terraform OIDC auth, Vault JWT, encrypted S3 state |
| **4** | Container Security | Multi-stage builds, non-root, Trivy CVE, Cosign signing, [`run-hardened.sh`](run-hardened.sh) |
| **5** | Kubernetes Security | RBAC, NetworkPolicies, Kyverno, PSA, Vault + ESO, etcd encryption, audit logging |

## Kubernetes Security Highlights

- **Namespaces with Pod Security Admission (PSA)** — `restricted` enforcement on all namespaces (`k8s/namespaces.yaml`)
- **Per-component ServiceAccounts** — `vote-sa`, `result-sa`, `worker-sa`, `db-sa`, `redis-sa` with `automountServiceAccountToken: false` (`k8s/serviceaccount-voting-app.yaml`)
- **Zero-Trust NetworkPolicies** — Default-deny + per-service allow rules (`k8s/networkpolicies.yaml`)
- **Kyverno Policies** — Enforce non-root, resource limits, no privilege escalation, image signing verification (`k8s/kyverno-policies.yaml`)
- **Pod Security Contexts** — All pods: `runAsNonRoot`, `readOnlyRootFilesystem`, `drop: ["ALL"]`, `seccompProfile: RuntimeDefault`
- **Gateway API** — Envoy-backed routing for `/vote` and `/result` endpoints
- **HPA + PDB** — Horizontal Pod Autoscaler and Pod Disruption Budgets for resilience (`k8s/hpa-pdb.yaml`)

## AI SRE Agent

An autonomous Kubernetes observability agent deployed in the `voting-agent` namespace with read-only RBAC:

- **Stack:** FastAPI + LangGraph + Google Gemini + Guardrails AI
- **MCP Integration:** Exposes `ask_k8s_assistant` tool for IDE integration (Cursor, Claude, etc.)
- **Features:** Natural language cluster queries, rate limiting, conversation history, input/output guardrails, SSE streaming
- **Docs:** [`agent/README.md`](agent/README.md)

## Quick Start (Local)

### Option 1: Kubernetes (kind) — Recommended

```bash
# 1. Create the kind cluster
kind create cluster --config k8s/kind-config.yaml --name voting-app-stable

# 2. Apply namespaces and RBAC
kubectl apply -f k8s/namespaces.yaml
kubectl apply -f k8s/serviceaccount-voting-app.yaml

# 3. Install Vault and External Secrets Operator (via Helm)
helm install vault hashicorp/vault -n default
helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace

# 4. Configure Vault secrets and apply ESO sync
kubectl apply -f k8s/external-secrets.yaml

# 5. Deploy the application stack
kubectl apply -f k8s/deployment-db.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/vote-deployment.yaml
kubectl apply -f k8s/result-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml

# 6. Apply services
kubectl apply -f k8s/db-service.yaml
kubectl apply -f k8s/redis-service.yaml
kubectl apply -f k8s/vote-service.yaml
kubectl apply -f k8s/result-service.yaml

# 7. Apply security policies
kubectl apply -f k8s/networkpolicies.yaml
```

### Option 2: Docker Compose (Development only)

```bash
# Copy environment file
cp agent/.env.example agent/.env  # Edit with your values

# Run with prebuilt images
docker compose -f docker-compose.images.yml up

# Or build from source
docker compose up --build
```

### Option 3: Hardened Docker (Agent only)

```bash
# Runs with: read-only FS, dropped capabilities, non-root, memory limits
bash run-hardened.sh
```

## Observability

![Grafana diagram](grafana.png)
![Prometheus diagram](prometheus.png)

## Repository Structure

```
├── agent/                  # AI SRE Agent (FastAPI + LangGraph)
│   ├── app/                # Application code
│   ├── k8s/                # Agent-specific K8s manifests
│   ├── terraform/          # IaC for AWS + Vault
│   └── skills/             # MCP skill definitions
├── k8s/                    # Kubernetes manifests (hardened)
│   ├── external-secrets.yaml    # Vault ↔ K8s secret sync
│   ├── networkpolicies.yaml     # Zero-trust network rules
│   ├── serviceaccount-voting-app.yaml  # RBAC
│   ├── kyverno-policies.yaml    # Admission policies
│   ├── namespaces.yaml          # PSA-enforced namespaces
│   └── *-deployment.yaml        # Hardened workloads
├── vote/                   # Vote microservice (Python)
├── result/                 # Result microservice (Node.js)
├── worker/                 # Worker microservice (.NET)
├── .github/                # CI/CD workflows + Dependabot
├── DEVSECOPS_STATUS.md     # 5-day implementation tracker
├── THREAT_MODEL.md         # STRIDE threat analysis
├── PRODUCTION_GUIDE.md     # Production deployment guide
└── run-hardened.sh         # Hardened Docker runtime script
```

## Security Before You Push to GitHub

- **`agent/.env` is gitignored** — it must stay local. Only `agent/.env.example` (placeholders) belongs in the repo.
- Before `git add`, run:

  ```bash
  git status
  git check-ignore -v agent/.env
  ```

- **Do not commit**: API keys, database passwords, kubeconfig files, or any token/secret values.
- **If a secret was ever committed**, rotate it immediately and treat the old value as compromised.

## Credits

Inspired by the classic **Docker example-voting-app** architecture and extended with DevSecOps, Kubernetes security, and AI-powered observability.

**Aapke DevOps Wale Bhaiya** — [TrainWithShubham](https://www.trainwithshubham.com/)
