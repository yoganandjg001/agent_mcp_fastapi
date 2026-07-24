# Application Startup Guide

This document provides step-by-step instructions on how to start the **Agentic Ops Assistant** system, including running the **MCP Server as an independent, standalone service BEFORE starting FastAPI**, as well as using the **unified orchestrator script (`run_integrated.py`)**.

---

## 📋 Prerequisites & Environment Setup

Before starting the application, ensure your environment is configured:

1. **Activate Virtual Environment (PowerShell)**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If script execution is blocked, run this once in PowerShell:
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```

2. **Verify Environment Variables (`.env`)**:
   Ensure a `.env` file exists in the root directory with required settings:
   ```env
   GROQ_API_KEY=gsk_...
   JWT_SECRET_KEY=agentic_ai_hackathon_super_secret_key_2026
   JWT_ALGORITHM=HS256
   TOKEN_EXPIRATION_SECONDS=3600
   FASTAPI_HOST=0.0.0.0
   FASTAPI_PORT=8000
   FASTAPI_BASE_URL=http://127.0.0.1:8000
   MCP_SERVER_URL=http://127.0.0.1:8001/sse
   MCP_TRANSPORT=sse
   ```

3. **Install Dependencies** (if not already installed):
   ```powershell
   pip install -r requirements.txt
   ```

---

## 🚀 Method 1: Single-Command Integrated Startup (`run_integrated.py`)

The simplest way to start the entire system is using `run_integrated.py`. It launches all 3 decoupled services sequentially in the correct dependency order:

```powershell
python run_integrated.py
```

### Order of Execution:
1. **MCP Server (Port 8001)**: Starts `python backend/mcp_service/mcp_server.py` as an independent SSE server on `http://localhost:8001/sse`.
2. **FastAPI Backend (Port 8000)**: Starts `uvicorn backend.api.fastapi_app:app` on `http://localhost:8000`.
3. **Streamlit Frontend (Port 8501)**: Starts `streamlit run frontend/streamlit_app.py` on `http://localhost:8501`.

Pressing `Ctrl+C` cleanly shuts down all three background processes.

---

## 🛠️ Method 2: Individual Python Commands (Multi-Terminal Startup)

To run services independently without depending on FastAPI to launch the MCP Server, start the services in separate terminal windows in the following order:

### 🔌 Step 1: Start Independent MCP Server (Terminal 1)

From the project root directory:

```powershell
.\.venv\Scripts\Activate.ps1
python backend/mcp_service/mcp_server.py
```

*Starts standalone MCP Server on `http://localhost:8001/sse`.*

---

### ⚙️ Step 2: Start FastAPI Backend Service (Terminal 2)

From the project root directory:

```powershell
.\.venv\Scripts\Activate.ps1

# Option A: Python Module Execution (Recommended)
python -m uvicorn backend.api.fastapi_app:app --host 0.0.0.0 --port 8000 --reload

# Option B: Direct Uvicorn CLI
uvicorn backend.api.fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

*FastAPI starts on `http://localhost:8000` and automatically connects to the running MCP Server at `http://localhost:8001/sse`.*

---

### 🎨 Step 3: Start Streamlit Frontend Dashboard (Terminal 3)

From the project root directory:

```powershell
.\.venv\Scripts\Activate.ps1

# Option A: Python Module Execution (Recommended)
python -m streamlit run frontend/streamlit_app.py --server.port 8501

# Option B: Direct Streamlit CLI
streamlit run frontend/streamlit_app.py --server.port 8501
```

*Streamlit Web Dashboard starts on `http://localhost:8501`.*

---

## 🧪 Method 3: Running Component-Level Python Tests

You can run component-specific scripts independently to verify isolated functionality:

```powershell
# 1. Test MCP Server (Direct Tool Executions)
$env:PYTHONPATH = ".;backend"
python tests/test_mcp_server.py

# 2. Test MCP Client (SSE / Stdio Protocol Connection)
python tests/test_mcp_client.py

# 3. Test LangGraph Agent & HITL Approvals
python tests/test_agent.py

# 4. Test FastAPI Auth & RBAC Endpoints
python tests/test_fastapi.py

# 5. Test Full Integrated Stack End-to-End
python tests/test_integration.py
```

Optional cleanup after tests:
```powershell
Remove-Item Env:PYTHONPATH
```

---

## 🧩 Architecture & Service Ports Summary

```
  ┌─────────────────────────────────────────────────────────────┐
  │                    Streamlit Dashboard                      │ (Port 8501)
  └──────────────────────────────┬──────────────────────────────┘
                                 │ HTTP API Requests + JWT Header
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                       FastAPI Service                       │ (Port 8000)
  └──────────────────────────────┬──────────────────────────────┘
                                 │ Internal Manager Orchestration
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                    LangGraph Agent Engine                   │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ Tool Calls via MCP Client
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                        MCP Client                           │ (mcp_service/mcp_client.py)
  └──────────────────────────────┬──────────────────────────────┘
                                 │ SSE Protocol (http://127.0.0.1:8001/sse)
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                   Standalone MCP Server                     │ (Port 8001)
  └──────────────────────────────┬──────────────────────────────┘
                                 │ File I/O Operations
                                 ▼
                   JSON Operational Databases 
           (servers.json, orders.json, tickets.json, users.json)
```

---

## 🔍 Service Ports Quick Reference

| Service | Script / Command | Host & Port |
| :--- | :--- | :--- |
| **MCP Server** | `python backend/mcp_service/mcp_server.py` | `http://localhost:8001/sse` |
| **FastAPI Backend** | `python -m uvicorn backend.api.fastapi_app:app --port 8000` | `http://localhost:8000` |
| **Streamlit Dashboard** | `python -m streamlit run frontend/streamlit_app.py --server.port 8501` | `http://localhost:8501` |
