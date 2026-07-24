import os
import json
import re
from typing import List, Dict, Any, Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_groq import ChatGroq

from mcp_service.mcp_client import mcp_client

# Load Environment Variables from .env file
load_dotenv()

# Define Sensitive Tools requiring Human-in-the-Loop Approval
SENSITIVE_TOOLS = {"restart_server", "process_refund", "escalate_ticket"}

# Initialize Primary LLM (ChatGroq llama-3.1-8b-instant)
groq_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    groq_api_key=groq_key,
    temperature=0
) if groq_key else None

# ---------------------------------------------------------------------
# 1. AGENT STATE DEFINITION
# ---------------------------------------------------------------------

class AgentState(TypedDict):
    """LangGraph State Schema preserving memory across turns."""
    messages: List[BaseMessage]
    session_id: str
    pending_approval: Optional[Dict[str, Any]]
    status: str  # "executing_safe", "awaiting_approval", "executing_sensitive", "rejected", "completed"
    last_response: Optional[str]
    current_tool_call: Optional[Dict[str, Any]]

# ---------------------------------------------------------------------
# 2. DYNAMIC MCP TOOL DISCOVERY VIA LLM
# ---------------------------------------------------------------------

def get_mcp_tool_schemas() -> List[Dict[str, Any]]:
    """Dynamically retrieves all tool schemas from MCP Server for LLM function binding."""
    mcp_tools = mcp_client.list_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t.get("input_schema") or t.get("inputSchema", {})
            }
        }
        for t in mcp_tools
    ]

SYSTEM_PROMPT = SystemMessage(content="""You are an IT & Operations Assistant.
You have access to tools from the Model Context Protocol (MCP) server:
- check_server_health: Check status and metrics of servers.
- get_ticket_status: Check IT support ticket status.
- calculate_refund: Calculate refund eligibility.
- process_refund: Process an order refund (SENSITIVE ACTION).
- restart_server: Restart a server (SENSITIVE ACTION).
- escalate_ticket: Escalate an IT support ticket (SENSITIVE ACTION).

Select appropriate tools to fulfill user requests.""")

def fallback_heuristic_parser(messages: List[BaseMessage]) -> Dict[str, Any]:
    """Standalone Fallback Heuristic Parser using regex entity matching when LLM is offline."""
    last_text = next((m.content.lower() for m in reversed(messages) if isinstance(m, HumanMessage)), "")

    if "restart" in last_text or "reboot" in last_text:
        m = re.search(r"([a-z0-9]+-(?:prod|staging|dev)-[0-9]+)", last_text)
        return {"type": "tool_call", "name": "restart_server", "args": {"server_name": m.group(1) if m else "auth-prod-01"}}

    if "refund" in last_text or "ord-" in last_text:
        m_id = re.search(r"(ord-\d+)", last_text)
        order_id = m_id.group(1).upper() if m_id else "ORD-5001"
        if any(k in last_text for k in ["calculate", "check", "eligible", "how much"]):
            return {"type": "tool_call", "name": "calculate_refund", "args": {"order_id": order_id}}
        m_amt = re.search(r"(?:amount\s*|\$)?(\d+(?:\.\d+)?)", last_text.replace(order_id.lower(), ""))
        return {"type": "tool_call", "name": "process_refund", "args": {"order_id": order_id, "amount": float(m_amt.group(1)) if m_amt else 10.0}}

    if "health" in last_text or "cpu" in last_text or "status" in last_text:
        m = re.search(r"([a-z0-9]+-(?:prod|staging|dev)-[0-9]+)", last_text)
        return {"type": "tool_call", "name": "check_server_health", "args": {"server_name": m.group(1)} if m else {}}

    if "escalate" in last_text:
        m = re.search(r"(tck-\d+)", last_text)
        return {"type": "tool_call", "name": "escalate_ticket", "args": {"ticket_id": m.group(1).upper() if m else "TCK-1001", "priority": "critical"}}

    if "ticket" in last_text or "tck-" in last_text:
        m = re.search(r"(tck-\d+)", last_text)
        return {"type": "tool_call", "name": "get_ticket_status", "args": {"ticket_id": m.group(1).upper()} if m else {}}

    return {"type": "text", "content": "I am your Ops Assistant. How can I help you today?"}

def _query_llm_intent(messages: List[BaseMessage]) -> Dict[str, Any]:
    """Queries ChatGroq with dynamic MCP tools, delegating to fallback_heuristic_parser on error."""
    if llm:
        try:
            llm_with_tools = llm.bind_tools(get_mcp_tool_schemas())
            res = llm_with_tools.invoke([SYSTEM_PROMPT] + list(messages))
            if res.tool_calls:
                tc = res.tool_calls[0]
                return {"type": "tool_call", "name": tc["name"], "args": tc["args"]}
            if res.content:
                return {"type": "text", "content": res.content.strip()}
        except Exception as e:
            print(f"[Agent Warning] ChatGroq LLM invocation failed, using simple fallback parser: {e}")

    return fallback_heuristic_parser(messages)

# ---------------------------------------------------------------------
# 3. LANGGRAPH NODES WITH VERBOSE FLOW PRINT STATEMENTS
# ---------------------------------------------------------------------

def router_node(state: AgentState) -> Dict[str, Any]:
    """
    [NODE 1: ENTRY / ROUTER NODE]
    Queries LLM with dynamic MCP tools. Classifies tool call as Safe vs Sensitive.
    """
    print("\n==================================================")
    print("🚀 [GRAPH FLOW] START ➔ router_node")
    print("==================================================")
    print("🤖 [ROUTER NODE] Evaluating user query and dynamic MCP tools...")

    intent = _query_llm_intent(state["messages"])

    if intent["type"] == "tool_call":
        tool_name, tool_args = intent["name"], intent["args"]
        tool_call_obj = {"name": tool_name, "args": tool_args}
        print(f"🎯 [LLM INTENT DETECTED] Tool Call: '{tool_name}' | Arguments: {tool_args}")

        if tool_name in SENSITIVE_TOOLS:
            print(f"🔒 [SECURITY CHECK] Tool '{tool_name}' is SENSITIVE (Requires HITL Approval)")
            print("➡️ [ROUTER BRANCH] Setting status: 'awaiting_approval'")
            return {
                "status": "awaiting_approval",
                "current_tool_call": tool_call_obj,
                "pending_approval": {
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "description": f"Request to execute sensitive action '{tool_name}' with args {tool_args}"
                }
            }
        print(f"🟢 [SECURITY CHECK] Tool '{tool_name}' is SAFE (Auto-execution permitted)")
        print("➡️ [ROUTER BRANCH] Setting status: 'executing_safe'")
        return {"status": "executing_safe", "current_tool_call": tool_call_obj}

    print("💬 [ROUTER BRANCH] Conversational text response generated. Setting status: 'completed'")
    txt = intent.get("content", "How can I assist you with operations today?")
    return {"messages": [AIMessage(content=txt)], "status": "completed", "last_response": txt}

def mcp_executor_node(state: AgentState) -> Dict[str, Any]:
    """
    [NODE 2: SAFE TOOL EXECUTOR NODE]
    Invokes non-sensitive read-only queries directly on the MCP Server.
    """
    print("\n==================================================")
    print("⚙️ [GRAPH FLOW] Entering mcp_executor_node")
    print("==================================================")
    tool = state.get("current_tool_call") or {}
    t_name = tool.get("name")
    t_args = tool.get("args", {})

    print(f"🔌 [MCP CLIENT] Invoking safe tool '{t_name}' on MCP Server with args {t_args}...")
    tool_output = mcp_client.call_tool(t_name, t_args)
    print(f"📥 [MCP CLIENT RESPONSE] Received output from MCP Server for '{t_name}'")

    try:
        formatted = f"```json\n{json.dumps(json.loads(tool_output), indent=2)}\n```"
    except Exception:
        formatted = tool_output

    print("🏁 [GRAPH FLOW] mcp_executor_node finished ➔ END")
    return {
        "messages": [ToolMessage(content=tool_output, tool_call_id="call_safe"), AIMessage(content=formatted)],
        "status": "completed",
        "last_response": formatted
    }

def approval_node(state: AgentState) -> Dict[str, Any]:
    """
    [NODE 3: HUMAN-IN-THE-LOOP APPROVAL NODE]
    Pauses graph execution natively using interrupt(). Waits for /approve via Command(resume=...).
    """
    print("\n==================================================")
    print("⚠️ [GRAPH FLOW] Entering approval_node")
    print("==================================================")
    print("⏳ [HITL PAUSE STATE] Graph execution is PAUSED natively via interrupt(). Awaiting /approve endpoint...")

    pending = state.get("pending_approval") or {}
    print(f"📩 [PENDING ACTION PAYLOAD] Tool: '{pending.get('tool_name')}' | Args: {pending.get('arguments')}")

    # LangGraph Native Interrupt
    resume_val = interrupt(pending)
    print(f"\n🛡️ [INTERRUPT RESUMED] Received resumption signal: '{resume_val}'")

    action = str(resume_val).lower()
    is_approved = action in ("approve", "approved", "yes")

    if is_approved:
        print("✅ [APPROVAL GRANTED] Setting status: 'executing_sensitive'")
        return {"status": "executing_sensitive"}
    else:
        print("🛑 [APPROVAL REJECTED] Setting status: 'rejected'")
        return {"status": "rejected"}

def resume_execution_node(state: AgentState) -> Dict[str, Any]:
    """
    [NODE 4: RESUME SENSITIVE EXECUTION NODE]
    Executes sensitive tool on MCP Server after human approval.
    """
    print("\n==================================================")
    print("⚡ [GRAPH FLOW] Entering resume_execution_node")
    print("==================================================")
    pending = state.get("pending_approval") or {}
    tool_name, tool_args = pending.get("tool_name"), pending.get("arguments", {})

    print(f"🔌 [MCP CLIENT (APPROVED)] Executing sensitive action '{tool_name}' on MCP Server with args {tool_args}...")
    tool_output = mcp_client.call_tool(tool_name, tool_args)
    print(f"📥 [MCP CLIENT RESPONSE] Execution successful for sensitive tool '{tool_name}'")

    try:
        formatted = f"```json\n{json.dumps(json.loads(tool_output), indent=2)}\n```"
    except Exception:
        formatted = tool_output

    msg = f"✅ **Request Approved & Executed**\n\n**Action:** `{tool_name}`\n**Status:** Completed\n\n**Final Details:**\n{formatted}"
    print("🏁 [GRAPH FLOW] resume_execution_node finished ➔ END")
    return {"messages": [AIMessage(content=msg)], "pending_approval": None, "status": "completed", "last_response": msg}

def rejection_node(state: AgentState) -> Dict[str, Any]:
    """
    [NODE 5: REJECTION NODE]
    Handles cancelled sensitive actions when human rejects request.
    """
    print("\n==================================================")
    print("🛑 [GRAPH FLOW] Entering rejection_node")
    print("==================================================")
    pending = state.get("pending_approval") or {}
    tool_name = pending.get("tool_name", "Action")
    print(f"🚫 [ACTION CANCELLED] Sensitive action '{tool_name}' was rejected by approver.")

    msg = f"🛑 **Request Rejected**\n\n**Action:** `{tool_name}`\n**Status:** Cancelled\n\n**Final Details:** The request to execute `{tool_name}` was rejected by the approver."
    print("🏁 [GRAPH FLOW] rejection_node finished ➔ END")
    return {"messages": [AIMessage(content=msg)], "pending_approval": None, "status": "rejected", "last_response": msg}

# ---------------------------------------------------------------------
# 4. CONDITIONAL ROUTERS WITH FLOW PRINT STATEMENTS
# ---------------------------------------------------------------------

def route_router_decision(state: AgentState) -> str:
    status = state.get("status")
    print(f"\n🔀 [CONDITIONAL EDGE 1] Evaluating router status: '{status}'")
    if status == "executing_safe":
        print("➡️ [DESTINATION] Routing to 'mcp_executor_node'")
        return "mcp_executor_node"
    elif status == "awaiting_approval":
        print("➡️ [DESTINATION] Routing to 'approval_node'")
        return "approval_node"
    print("➡️ [DESTINATION] Routing to END")
    return END

def route_approval_decision(state: AgentState) -> str:
    status = state.get("status")
    print(f"\n🔀 [CONDITIONAL EDGE 2] Evaluating approval status: '{status}'")
    if status == "executing_sensitive":
        print("➡️ [DESTINATION] Routing to 'resume_execution_node'")
        return "resume_execution_node"
    elif status == "rejected":
        print("➡️ [DESTINATION] Routing to 'rejection_node'")
        return "rejection_node"
    print("➡️ [DESTINATION] Routing to END")
    return END

# ---------------------------------------------------------------------
# 5. STATE GRAPH COMPILATION WITH PERSISTENCE CHECKPOINTER
# ---------------------------------------------------------------------

builder = StateGraph(AgentState)

# Add Nodes
builder.add_node("router_node", router_node)
builder.add_node("mcp_executor_node", mcp_executor_node)
builder.add_node("approval_node", approval_node)
builder.add_node("resume_execution_node", resume_execution_node)
builder.add_node("rejection_node", rejection_node)

# Add Edges & Conditional Routing
builder.add_edge(START, "router_node")
builder.add_conditional_edges("router_node", route_router_decision)
builder.add_conditional_edges("approval_node", route_approval_decision)

builder.add_edge("mcp_executor_node", END)
builder.add_edge("resume_execution_node", END)
builder.add_edge("rejection_node", END)

# Compile Graph with In-Memory Checkpointer
simple_agent_graph = builder.compile(checkpointer=MemorySaver())

# ---------------------------------------------------------------------
# 6. AGENT MANAGER INTERFACE (For FastAPI & Streamlit Integration)
# ---------------------------------------------------------------------

class LangGraphAgentManager:
    """Manager Interface connecting FastAPI endpoints (/chat, /approve, /status)."""

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def run_message(self, session_id: str, message: str, username: str = "user") -> Dict[str, Any]:
        config = {"configurable": {"thread_id": session_id}}
        init_state = {
            "messages": [HumanMessage(content=message)],
            "session_id": session_id,
            "pending_approval": None,
            "status": "init",
            "last_response": None,
            "current_tool_call": None
        }

        final_state = simple_agent_graph.invoke(init_state, config=config)
        snapshot = simple_agent_graph.get_state(config)
        
        status = final_state.get("status", "completed")
        pending = final_state.get("pending_approval")

        if snapshot.next and "approval_node" in snapshot.next:
            status = "awaiting_approval"
            if snapshot.tasks and snapshot.tasks[0].interrupts:
                pending = snapshot.tasks[0].interrupts[0].value

        resp = final_state.get("last_response")
        if not resp and status == "awaiting_approval" and pending:
            resp = f"📩 **Request sent for approval**\n\n- **Action:** `{pending.get('tool_name')}`\n- **Status:** ⏳ *Pending Approval by Approver*"

        # Dynamically compute exact node history trajectory
        if status == "awaiting_approval":
            history = ["router_node", "approval_node"]
        elif final_state.get("current_tool_call"):
            history = ["router_node", "mcp_executor_node", "completed"]
        else:
            history = ["router_node", "completed"]

        result = {
            "session_id": session_id,
            "status": status,
            "pending_approval": pending,
            "response": resp or "Request processed.",
            "username": username,
            "node_history": history
        }

        self.active_sessions[session_id] = {
            "username": username,
            "last_message": message,
            "status": status,
            "pending_approval": pending,
            "node_history": history
        }

        return result

    def process_approval(self, session_id: str, action: str, approver_username: str = "approver") -> Dict[str, Any]:
        config = {"configurable": {"thread_id": session_id}}
        snapshot = simple_agent_graph.get_state(config)

        if not snapshot.next or "approval_node" not in snapshot.next:
            return {"session_id": session_id, "status": "error", "response": "No pending action found for this session."}

        final_state = simple_agent_graph.invoke(Command(resume=action), config=config)
        status = final_state.get("status", "completed")
        pending = final_state.get("pending_approval")
        resp = final_state.get("last_response", "Action processed.")

        # Dynamically compute exact node history after approval/rejection
        if status == "rejected":
            history = ["router_node", "approval_node", "rejection_node", "rejected"]
        else:
            history = ["router_node", "approval_node", "resume_execution_node", "completed"]

        if session_id in self.active_sessions:
            self.active_sessions[session_id]["status"] = status
            self.active_sessions[session_id]["pending_approval"] = pending
            self.active_sessions[session_id]["node_history"] = history

        return {
            "session_id": session_id,
            "status": status,
            "pending_approval": pending,
            "response": resp,
            "approver": approver_username,
            "node_history": history
        }

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        config = {"configurable": {"thread_id": session_id}}
        snapshot = simple_agent_graph.get_state(config)
        if not snapshot.values:
            return None
        
        status = snapshot.values.get("status", "completed")
        pending = snapshot.values.get("pending_approval")
        if snapshot.next and "approval_node" in snapshot.next:
            status = "awaiting_approval"
            if snapshot.tasks and snapshot.tasks[0].interrupts:
                pending = snapshot.tasks[0].interrupts[0].value

        history = snapshot.values.get("node_history", [])
        if not history and session_id in self.active_sessions:
            history = self.active_sessions[session_id].get("node_history", ["router_node"])

        return {
            "session_id": session_id,
            "status": status,
            "pending_approval": pending,
            "last_response": snapshot.values.get("last_response"),
            "node_history": history,
            "messages_count": len(snapshot.values.get("messages", []))
        }

    def list_all_pending_approvals(self) -> List[Dict[str, Any]]:
        """Returns all active sessions currently awaiting approval."""
        pending_list = []
        for sid, sess in list(self.active_sessions.items()):
            status_info = self.get_session_status(sid)
            if status_info and status_info.get("status") == "awaiting_approval" and status_info.get("pending_approval"):
                pending_list.append({
                    "session_id": sid,
                    "username": sess.get("username", "user"),
                    "status": "awaiting_approval",
                    "pending_approval": status_info["pending_approval"]
                })
        return pending_list

    def list_all_user_sessions(self) -> List[Dict[str, Any]]:
        """Returns metadata for all user sessions."""
        return [{"session_id": sid, **meta} for sid, meta in self.active_sessions.items()]

agent_manager = LangGraphAgentManager()
