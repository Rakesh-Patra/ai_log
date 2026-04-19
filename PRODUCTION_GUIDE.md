# 🛡️ Production Readiness Guide (Senior DevOps)

This document provides the roadmap for transitioning this stack from local development/learning to a production-grade enterprise environment.

## 1. 🔑 Secrets & Authentication Hardening

The most critical step for production is moving away from local `.env` files and "dev-bypass" logic.

### AI Agent Security
- **Mode**: Set `APP_ENV=prod` in your environment. This disables the "dev-bypass" in `auth.py`.
- **API Key**: Set a strong binary-generated `API_AUTH_KEY`. 
- **Header**: Ensure all clients send this key in the `X-API-Key` header.

### Infrastructure Secrets
- **Vault**: Transition all static Kubernetes Secrets to **HashiCorp Vault**. Use the **Vault Agent Sidecar** to inject secrets directly into the pods without them ever touching your Git repository.
- **ServiceAccounts**: Never use the `default` ServiceAccount. Each service (`vote`, `result`, `worker`, `agent`) must have its own dedicated ServiceAccount with minimal RBAC permissions.

## 2. 🌐 Networking & Traffic Management

### CORS & Origin Security
- Update the `CORS_ORIGINS` variable in `agent/app/config.py` (via environment) to only include your official production domain.
- **Do not use `*` (wildcard) in production.**

### SSL / TLS
- Deploy **cert-manager** in your cluster.
- Use the **Kubernetes Gateway API** (Envoy) to handle SSL termination. All traffic must be HTTPS (Port 443).

### Load Balancing
- Use a Cloud Load Balancer (AWS ALB, etc.) in front of your Kind/K8s cluster to handle external traffic and provide DDoS protection.

## 3. 📈 Reliability & Scaling

### Redundancy
- **Replicas**: Set `replicas: 3` for all core services to ensure high availability.
- **Anti-Affinity**: Use Pod Anti-Affinity rules to ensure replicas of the same service run on different physical nodes.

### Resource Management
- **Quotas**: Every pod must have `resources.requests` and `resources.limits` defined for CPU and Memory to prevent a single pod from crashing the entire node.
- **HPA**: Enable **Horizontal Pod Autoscaling** based on CPU/Memory usage or custom metrics (e.g., AI Agent request latency).

## 4. 📊 Observability (AIOps)

### Centralized Logging
- Ship all JSON-formatted logs from `structlog` to a centralized store like **Grafana Loki** or **Elasticsearch**.
- Monitor for the `INSECURE_MODE` or `auth_failed` log events.

### Metrics & Dashboarding
- Install **Prometheus** and **Grafana**.
- Create a dashboard for the AI Agent showing:
    - Tool invocation success rate.
    - Token usage (Gemini costs).
    - Request latency (P95).

## 5. 🚀 Continuous Delivery (GitOps)

### Argo CD
- Use the existing `k8s/` manifests within an **Argo CD Application**.
- Enable **Automated Pruning** and **Self-Healing** so that the cluster state always matches the `main` branch.

### Deployment Strategies
- Transition from "Recreate" to **RollingUpdate**.
- For the AI Agent, consider **Canary Deployments** to test new model prompts on 5% of traffic before a full rollout.

---

*This guide was prepared by your Senior DevOps AI Assistant.*
