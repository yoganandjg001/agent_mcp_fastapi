import os
import sys
import json
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure api, backend, and project root directories are in sys.path
api_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(api_dir)
project_root = os.path.dirname(backend_dir)
for d in [api_dir, backend_dir, project_root]:
    if d not in sys.path:
        sys.path.insert(0, d)

# Load Environment Variables from .env file
load_dotenv()

from agent import agent_manager
from mcp_service.mcp_client import mcp_client
from auth import (
    LoginRequest,
    LoginResponse,
    create_jwt_token,
    get_current_user,
    require_approver_role
)

app = FastAPI(
    title="Agentic Ops Assistant API",
    description="FastAPI service exposing LangGraph Agent & MCP capabilities with JWT Security",
    version="1.0.0"
)

# --- REQUEST SCHEMAS ---

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ApproveRequest(BaseModel):
    session_id: str
    action: str  # "approve" or "reject"

# --- ENDPOINTS ---

@app.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """Authenticate user credentials via MCP Client user validation tool and return JWT."""
    res_str = mcp_client.call_tool("validate_user_login", {"username": req.username, "password": req.password})
    val_data = json.loads(res_str)
    
    if not val_data.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=val_data.get("error", "Invalid username or password")
        )
    
    token_data = {
        "sub": val_data["username"],
        "full_name": val_data["full_name"],
        "role": val_data["role"]
    }
    token = create_jwt_token(token_data)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        username=val_data["username"],
        full_name=val_data["full_name"],
        role=val_data["role"]
    )

@app.post("/chat")
def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Send a user message to the LangGraph Agent (JWT-protected)."""
    response = agent_manager.run_message(req.session_id, req.message, username=current_user["sub"])
    response["user"] = current_user["sub"]
    return response

@app.post("/approve")
def approve(req: ApproveRequest, current_user: dict = Depends(get_current_user)):
    """Approve or reject a pending sensitive action in LangGraph (JWT-protected + Role Check)."""
    require_approver_role(current_user)
    response = agent_manager.process_approval(req.session_id, req.action, approver_username=current_user["sub"])
    response["approver"] = current_user["sub"]
    return response

@app.get("/pending_approvals")
def get_pending_approvals(current_user: dict = Depends(get_current_user)):
    """Retrieve all pending approvals across the system for Approvers."""
    return agent_manager.list_all_pending_approvals()

@app.get("/user_workflow_history")
def get_user_workflow_history(current_user: dict = Depends(get_current_user)):
    """Retrieve workflow execution history for all user sessions across the system."""
    require_approver_role(current_user)
    return agent_manager.list_all_user_sessions()

@app.get("/status/{session_id}")
def get_session_status(session_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve session conversation state and pending approval status (JWT-protected)."""
    return agent_manager.get_session_status(session_id)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "FastAPI Ops Service"}
