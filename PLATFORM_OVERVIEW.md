# 🛡️ AI-SRE: Next-Generation DevSecOps Platform
## *The Future of Autonomous Infrastructure & Security*

---

## 🌟 Executive Summary
This platform is a **Self-Healing, Zero-Trust AI Operations (AIOps) system**. It replaces traditional manual SRE tasks with an **Autonomous AI Agent** that reasons, acts, and secures Kubernetes infrastructure in real-time. 

Unlike standard monitoring tools (Datadog), this platform doesn't just alert you—it **remedies issues autonomously** while maintaining a hardened security posture.

---

## 🛠️ Technical Architecture

### 1. The Brain: AI SRE Agent
*   **Engine**: Google Gemini 2.5 Flash (via LangGraph).
*   **Capabilities**: Real-time cluster inspection, automated pod remediation, dynamic scaling, and interactive troubleshooting.
*   **Guardrails**: Built-in **Risk Analysis engine** that blocks high-risk or destructive actions unless explicitly approved by a human.

### 2. The Muscle: Durable Orchestration (Temporal)
*   **Reliability**: Every AI action is wrapped in a **Temporal Workflow**. 
*   **Durable Execution**: If a network failure occurs during a multi-step fix, Temporal ensures the AI resumes exactly where it left off. No more orphaned resources or half-finished automations.

### 3. The Shield: Zero-Trust Security (Vault)
*   **Dynamic Credentials**: No static AWS keys or Kubernetes tokens are stored in the code.
*   **Vault Integration**: Uses HashiCorp Vault to issue short-lived, just-in-time credentials for the Agent and CI/CD pipelines.
*   **OIDC Auth**: Fully passwordless authentication for GitHub Actions.

### 4. The Eyes: Observability (LangSmith & Prometheus)
*   **Traceability**: Every "thought" and tool call made by the AI is logged in **LangSmith** for full auditability.
*   **Metrics**: Real-time cluster health monitoring via **Prometheus**.

---

## 🚀 Key Features

| Feature | Description |
| :--- | :--- |
| **Self-Healing** | Automatically detects and fixes `CrashLoopBackOff`, `OOMKilled`, and `ImagePullBackOff` errors. |
| **Public AI Gateway** | Securely exposed REST API (`/agent`) protected by `API_AUTH_KEY` for global team use. |
| **IaC Automation** | Entire environment is provisioned on high-performance AWS `m7i-flex.large` via Terraform. |
| **Pluggable Design** | Can be ported to any Kubernetes application or cluster in under 5 minutes. |
| **Secret Syncing** | Automated secret rotation via the External Secrets Operator. |

---

## 🌐 Public Access Endpoints
*   **Voting Application**: [http://100.54.213.247/](http://100.54.213.247/)
*   **Real-time Results**: [http://100.54.213.247/result](http://100.54.213.247/result)
*   **AI Agent API**: [http://100.54.213.247/agent](http://100.54.213.247/agent)
*   **Security Dashboard**: [http://13.232.226.25:30200](http://13.232.226.25:30200)

---

## 📈 Value Proposition
1.  **Reduce MTTR (Mean Time To Recovery)**: AI fixes outages in seconds, not minutes.
2.  **Eliminate Secret Leaks**: 100% dynamic credentialing via Vault.
3.  **Scalable Operations**: One DevOps engineer can manage 10x more clusters with the help of the AI SRE.
4.  **Lower Costs**: Built on Open Source (K3s, Temporal, Vault) and efficient AWS ARM-compatible instances.

---

**Developed by: Rakesh Patra & Antigravity AI**
*Ready for Production Launch: April 30, 2026, 6:00 PM*
