# 🗳️ AI-Powered Kubernetes DevSecOps Platform

[![Kubernetes](https://img.shields.io/badge/Kubernetes-K3s-326CE5?logo=kubernetes&logoColor=white)](https://k3s.io/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform)](https://terraform.io/)
[![Python](https://img.shields.io/badge/Agent-Python_3.12-3776AB?logo=python&logoColor=white)](https://python.org/)
[![GitHub Actions](https://img.shields.io/badge/CI/CD-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![ArgoCD](https://img.shields.io/badge/GitOps-ArgoCD-EF7B4D?logo=argo&logoColor=white)](https://argoproj.github.io/argo-cd/)

> **Production-approach voting app with an autonomous AI SRE agent, 
> GitOps self-healing, 7-layer DevSecOps pipeline, LangSmith observability, 
> and $0 AWS infrastructure using K3s + m7i-flex.large.**

---

## 🏗️ Architecture (Phase 3)

```
                     ┌──────────────────────────────────────────────────────────────┐
                     │               GitHub Actions CI/CD Pipeline                  │
                     │   Gitleaks → Hadolint → Build → Trivy → Cosign → Terraform   │
                     └────────────────────────┬─────────────────────────────────────┘
                                              │
                     ┌────────────────────────▼─────────────────────────────────────┐
                     │          AWS EC2 m7i-flex.large ($0 — free credits)          │
                     │  ┌───────────────────────────────────────────────────────┐   │
                     │  │                    K3s Cluster                        │   │
                     │  │                                                      │   │
                     │  │  ┌──────────┐   ┌─────────┐   ┌─────────────┐        │   │
                     │  │  │  ArgoCD  │◄──│ Git Repo│──▶│ AI SRE Agent│        │   │
                     │  │  │ (GitOps) │   └─────────┘   │ (LangGraph) │        │   │
                     │  │  └────┬─────┘                 └──────▲──────┘        │   │
                     │  │       │                              │               │   │
                     │  │  ┌────▼─────┐   ┌───────┐   ┌────────▼─────────┐     │   │
                     │  │  │ App Pods │──▶│ Loki  │──▶│ Webhook Endpoint │     │   │
                     │  │  │ (Vote/etc)│   └───────┘   └────────▲─────────┘     │   │
                     │  │  └──────────┘                        │               │   │
                     │  │       ▲                              │               │   │
                     │  │       └──────────────────────────────┘               │   │
                     │  │          (Action: Restart/Scale Down)                │   │
                     │  │                                                      │   │
                     │  │  ┌──────────┐  ┌─────────┐  ┌──────────┐             │   │
                     │  │  │Prometheus│──▶│ Alertmgr│──┘ (Trigger)             │   │
                     │  │  └──────────┘  └─────────┘                           │   │
                     │  └───────────────────────────────────────────────────────┘   │
                     └──────────────────────────────────────────────────────────────┘
```

---

## ✨ Autonomous AI SRE & FinOps

This platform features **Sentinel-Ops**, a LangGraph-powered AI agent that acts as an autonomous L3 engineer.

| Feature | How It Works | Why It Matters |
|---------|--------------|----------------|
| **Auto-Triage** | Alertmanager → Webhook → Agent | 2am incidents are triaged in seconds, not hours. |
| **Log Analysis** | Agent queries Loki via OTLP | Finds the "needle in the haystack" stack trace automatically. |
| **FinOps Automation** | Agent scales idle pods to 0 | Eliminates cloud waste by identifying unused dev environments. |
| **GitOps Integrity** | ArgoCD + Self-Healing | Prevents manual drift; Git remains the source of truth. |

---

## 🔒 Phase 3 — Autonomous AIOps & GitOps

| Feature | Implementation | Why it matters |
|---|---|---|
| **AI Webhook** | FastAPI + LangGraph | Connects Prometheus alerts to autonomous action. |
| **Loki Tools** | Python + requests | Allows the agent to "see" application errors. |
| **FinOps Scaling** | `kubectl scale --replicas=0` | Active cost-cutting by scaling down idle resources. |
| **ArgoCD** | Helm + App-of-Apps | Implements true GitOps with auto-pruning. |
| **Kubecost** | Allocation & API | Real-time dollar-value cost tracking per namespace. |
| **Goldilocks** | Right-sizing Dashboard | Visualizes VPA recommendations for perfect pod sizing. |


### 🧪 How to Test Autonomous Remediation
1. **Simulate a Crash**: Delete a critical config or manually scale a deployment to 10 replicas.
2. **Watch ArgoCD**: Observe the ArgoCD UI as it detects the drift and force-syncs the cluster back to the Git state.
3. **Simulate a Budget Alert**: Send a mock JSON payload to the `/agent/webhook/alertmanager` endpoint indicating high cost.
4. **Watch the AI**: Check the agent logs as it queries Prometheus, identifies the `worker` namespace as idle, and scales the deployment to 0.

---

## 🚀 Quick Start (Phase 3)

```bash
# 1. Setup GitOps
ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/setup-argocd.yaml

# 2. Setup AI Tools
# Ensure LOKI_URL and PROMETHEUS_URL are set in the agent's .env

# 3. Trigger manual triage (Example)
curl -X POST http://<AGENT_IP>/agent/webhook/alertmanager \
     -d '{"alerts": [{"labels": {"alertname": "PodCrashLooping", "pod": "vote-app-xyz"}}] }'
```

---

## 🎯 Phase 2 & 3 Evolution

This project evolved from a standard DevSecOps pipeline into a self-healing, cost-aware autonomous platform. Choosing **Loki over ELK** and **K3s over EKS** were critical design decisions to maintain a **$0 running cost** on an 8GB RAM footprint while delivering enterprise-grade observability.

---

## 📚 Credits & Built By
- **Curriculum**: [Abhishek Veeramalla's DevSecOps-Zero-to-Hero](https://github.com/iam-veeramalla)
- **Built by**: [Rakesh Patra](https://linkedin.com/in/rakesh-patra) 🇮🇳
