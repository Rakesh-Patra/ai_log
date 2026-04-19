# 🚀 Kubernetes AI Agent

A production-ready Kubernetes AI agent powered by **LangGraph**, **Google Gemini**, and **Guardrails AI**, exposed via a **FastAPI** REST API.

## Architecture

```
agent/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py             # Settings (pydantic-settings)
│   ├── core/
│   │   ├── agent.py          # LangGraph ReAct agent factory
│   │   └── mcp_client.py     # MCP client & session management
│   ├── guardrails/
│   │   └── validators.py     # Input/output safety validators
│   ├── api/
│   │   ├── routes.py         # FastAPI route definitions
│   │   └── schemas.py        # Pydantic request/response models
│   └── utils/
│       └── logging.py        # Structured JSON logging
├── mcp_server.py             # 🆕 FastMCP server for IDE integration
├── run_mcp.bat               # Windows launcher for MCP
├── run_mcp.sh                # Linux/Mac launcher for MCP
├── test_mcp_call.py          # Verification script
├── .env.example        # Environment configuration
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Features

| Feature | Description |
|---|---|
| 🤖 **AI Agent** | LangGraph ReAct agent with Gemini model |
| 🛡️ **Guardrails AI** | Prompt injection detection, topic restriction, PII redaction |
| ⚡ **FastAPI Backend** | REST API with Swagger docs, SSE streaming |
| 💻 **IDE Integration** | **FastMCP** server for Cursor, Claude Desktop, and more |
| 📝 **Conversation History** | Multi-turn context tracking via InsForge |
| 📊 **Structured Logging** | JSON logs via structlog |
| 🔧 **Kubernetes Tools** | 22+ direct cluster management tools via MCP |

## Guardrails

### Input Guards
- **Prompt Injection Detection** – Blocks attempts to override system instructions
- **Topic Restriction** – Only allows Kubernetes/DevOps related queries
- **Toxic Language Filter** – Blocks harmful language

### Output Guards
- **PII Redaction** – Automatically redacts emails, IPs, tokens, keys, and secrets

## 💻 IDE Integration (via MCP)

You can use this agent directly in your IDE (Cursor, Claude Desktop, VS Code) using the **Model Context Protocol (MCP)**. This allows the AI in your editor to call your specialized Kubernetes agent to perform cluster operations.

### Windows (Cursor / Claude Desktop)
1. Ensure your `.env` is configured with `GOOGLE_API_KEY`.
2. Open your IDE's MCP settings.
3. Add a new command-based MCP server:
   - **Command**: `c:\ai_log\k8s-kind-voting-app\agent\run_mcp.bat`

### Linux / Mac
1. Configure your `.env`.
2. Add the MCP server in your IDE settings:
   - **Command**: `/path/to/k8s-kind-voting-app/agent/run_mcp.sh`

---

## Pull and Run from Docker Hub 🐳

The agent image is available on Docker Hub as `patracoder/k8s-ai-agent:v1.0`.

> [!TIP]
> This image is **multi-architecture** (`linux/amd64` and `linux/arm64`), meaning it works perfectly on regular servers as well as **Apple Silicon (M1/M2/M3)** Macs and ARM-based cloud instances.

### Run the Agent
To start the agent container, you must provide your Google API Key and mount your local `kubeconfig`:

```bash
docker run -d -p 8000:8000 \
  -e GOOGLE_API_KEY="your_google_api_key_here" \
  -v ~/.kube:/home/app/.kube \
  patracoder/k8s-ai-agent:v1.0
```

### Required Variables
| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | Your Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/). |
| `KUBECONFIG` | (Optional) Inside the container, set to `/home/app/.kube/config` by default. |

### Required Volumes
| Volume | Description |
|---|---|
| `~/.kube` | Mount your local `.kube` folder to `/home/app/.kube` so the agent can interact with your cluster. |

---

## Setup (Local Development)

### 1. Install dependencies

```bash
cd agent
python -m venv venv
source venv/bin/activate   # Linux/macOS/WSL
# Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Copy the example file and **never commit** the real `.env`:

```bash
# Linux / macOS / WSL
cp .env.example .env

# Windows (PowerShell)
copy .env.example .env
```

Edit `.env` — required and optional variables are documented in [`.env.example`](.env.example). Minimum for the API:

```env
GOOGLE_API_KEY=your_key_here
KUBECONFIG_PATH=/home/your_user/.kube/config
```

On Windows, use a path like `C:\Users\you\.kube\config` and set `NPX_PATH` to `npx` or the full path to `npx.cmd`.

**Before `git push`:** run `git check-ignore -v .env` — it must show this file as ignored. Do not add API keys, LangSmith keys, or DB passwords to any tracked file.

### 3. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | App info |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |
| `POST` | `/api/v1/query` | Send a query to the agent |
| `POST` | `/api/v1/query/stream` | Streaming response via SSE |
| `GET` | `/api/v1/history/{id}` | Get conversation history |
| `DELETE` | `/api/v1/history/{id}` | Clear conversation history |

## Usage Examples

### Query the agent
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "List all pods in the default namespace"}'
```

### Health check
```bash
curl http://localhost:8000/health
```

### Stream response
```bash
curl -N -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all deployments"}'
```

## Model

The default model is set in `app/config.py` (e.g. **Gemini** `gemini-2.5-flash-lite`); override with `MODEL_NAME` in `.env` if needed.
