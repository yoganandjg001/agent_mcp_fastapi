import os
import streamlit as st
import requests
import json
import uuid
import html
import textwrap
from dotenv import load_dotenv

# Load Environment Variables from .env file
load_dotenv()

# Configuration
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Agentic Ops Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics and maximum text visibility
st.markdown("""
<style>
    /* Dark glassmorphism container styling */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    .main-header {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.4);
    }
    .user-card {
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }
    .badge-approver {
        background-color: #059669;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-user {
        background-color: #3b82f6;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .approval-box {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.35) 100%);
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 0 25px rgba(239, 68, 68, 0.4);
    }
    .graph-card {
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid rgba(168, 85, 247, 0.4);
        border-radius: 12px;
        padding: 1.4rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .chat-bubble-user {
        background: rgba(79, 70, 229, 0.35);
        border: 1px solid rgba(99, 102, 241, 0.6);
        border-radius: 12px 12px 0px 12px;
        padding: 1rem;
        margin: 0.5rem 0 0.5rem auto;
        max-width: 80%;
        color: #ffffff;
    }
    .chat-bubble-ai {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px 12px 12px 0px;
        padding: 1rem;
        margin: 0.5rem auto 0.5rem 0;
        max-width: 85%;
        color: #ffffff;
    }
    .live-pulse {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse 1.5s infinite;
        margin-right: 6px;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .stTextInput label {
        color: #38bdf8 !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
    }

    /* Expander styling - Dark Glassmorphism */
    div[data-testid="stExpander"] {
        background-color: rgba(30, 41, 59, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px !important;
        color: #f8fafc !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        margin-bottom: 1rem !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: rgba(15, 23, 42, 0.8) !important;
        color: #38bdf8 !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
    }
    div[data-testid="stExpander"] summary:hover {
        color: #60a5fa !important;
        background-color: rgba(30, 41, 59, 1) !important;
    }
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        background-color: rgba(15, 23, 42, 0.95) !important;
        color: #f8fafc !important;
        padding: 1rem !important;
        border-radius: 0 0 10px 10px !important;
    }
    
    /* Global Code styling */
    code, pre, .stMarkdown code {
        background-color: rgba(15, 23, 42, 0.9) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 6px !important;
        padding: 2px 6px !important;
    }

    /* Button styling across application (includes form submit buttons) */
    .stButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
        background: #0f172a !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
    }
    .stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: #1e293b !important;
        border-color: #38bdf8 !important;
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }
    .stButton > button[kind="secondary"],
    div[data-testid="stFormSubmitButton"] > button[kind="secondary"] {
        background: rgba(239, 68, 68, 0.2) !important;
        color: #fca5a5 !important;
        border: 1px solid #ef4444 !important;
    }
    .stButton > button[kind="secondary"]:hover,
    div[data-testid="stFormSubmitButton"] > button[kind="secondary"]:hover {
        background: rgba(239, 68, 68, 0.4) !important;
        color: #ffffff !important;
    }

    /* Input fields styling */
    .stTextInput input {
        background-color: rgba(30, 41, 59, 0.9) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "token" not in st.session_state:
    st.session_state["token"] = ""
if "user_info" not in st.session_state:
    st.session_state["user_info"] = {}
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "pending_approval" not in st.session_state:
    st.session_state["pending_approval"] = None
if "current_status" not in st.session_state:
    st.session_state["current_status"] = "idle"
if "node_history" not in st.session_state:
    st.session_state["node_history"] = []

# --- NODE TRAJECTORY FORMATTER ---
NODE_LABEL_MAP = {
    "Start": "🚀 START",
    "router": "🔀 router_node",
    "router_node": "🔀 router_node",
    "mcp_executor_node": "⚙️ mcp_executor_node",
    "approval_node": "⚠️ approval_node (Interrupt)",
    "resume_execution_node": "⚡ resume_execution_node",
    "rejection_node": "🛑 rejection_node",
    "completed": "🏁 END",
    "rejected": "🛑 REJECTED & END"
}

def format_node_trajectory(node_list: list) -> str:
    """Formats raw LangGraph node history strings into clean, user-friendly operational trajectory steps."""
    if not node_list:
        return "🚀 START ➔ 🔀 router_node"
    
    raw_nodes = ["Start"] + [n for n in node_list if n != "Start"]
    clean_steps = []
    for node in raw_nodes:
        label = NODE_LABEL_MAP.get(node, node)
        if not clean_steps or clean_steps[-1] != label:
            clean_steps.append(label)
            
    return " ➔ ".join(clean_steps)

# --- UI ENRICHMENT RENDERERS ---

def render_enriched_card(data: dict) -> str:
    """Generates rich, vibrant HTML/CSS card representations for operational JSON data."""
    # 1. TICKET DATA
    if "ticket_id" in data:
        t_id = data.get("ticket_id", "")
        emp = data.get("employee", "N/A")
        subj = data.get("subject", "N/A")
        status = str(data.get("status", "open")).upper()
        priority = str(data.get("priority", "medium")).upper()
        assigned = data.get("assigned_to", "N/A")
        created = data.get("created_date", "N/A")

        p_color = "#ef4444" if priority in ["HIGH", "CRITICAL"] else "#f59e0b"
        s_color = "#10b981" if status in ["OPEN", "RESOLVED"] else "#3b82f6"

        return textwrap.dedent(f"""
        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95)); border: 1px solid rgba(99, 102, 241, 0.5); border-radius: 12px; padding: 1.25rem; margin: 0.75rem 0; box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
                <span style="font-size:1.1rem; font-weight:bold; color:#f8fafc;">🎫 Support Ticket <code style="color:#6366f1;">{html.escape(t_id)}</code></span>
                <div>
                    <span style="background:{p_color}; color:white; padding:3px 8px; border-radius:6px; font-size:0.75rem; font-weight:bold; margin-right:4px;">{priority}</span>
                    <span style="background:{s_color}; color:white; padding:3px 8px; border-radius:6px; font-size:0.75rem; font-weight:bold;">{status}</span>
                </div>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size:0.9rem; color:#cbd5e1;">
                <div><b>👤 Employee:</b> {html.escape(emp)}</div>
                <div><b>🛠️ Assigned:</b> {html.escape(assigned)}</div>
                <div><b>📅 Created:</b> {html.escape(created)}</div>
                <div><b>📋 Subject:</b> {html.escape(subj)}</div>
            </div>
        </div>
        """)

    # 2. SERVER DATA
    elif "server_name" in data:
        s_name = data.get("server_name", "")
        env = str(data.get("environment", "prod")).upper()
        status = str(data.get("status", "healthy")).upper()
        cpu = data.get("cpu_percent", 0)
        mem = data.get("memory_percent", 0)
        disk = data.get("disk_percent", 0)
        uptime = data.get("uptime_days", 0)

        s_bg = "#10b981" if status == "HEALTHY" else "#ef4444"

        return textwrap.dedent(f"""
        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95)); border: 1px solid rgba(16, 185, 129, 0.5); border-radius: 12px; padding: 1.25rem; margin: 0.75rem 0; box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
                <span style="font-size:1.1rem; font-weight:bold; color:#f8fafc;">🖥️ Server Health <code style="color:#10b981;">{html.escape(s_name)}</code></span>
                <div>
                    <span style="background:#64748b; color:white; padding:3px 8px; border-radius:6px; font-size:0.75rem; font-weight:bold; margin-right:4px;">ENV: {env}</span>
                    <span style="background:{s_bg}; color:white; padding:3px 8px; border-radius:6px; font-size:0.75rem; font-weight:bold;">{status}</span>
                </div>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; text-align:center;">
                <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:8px;">
                    <div style="font-size:0.75rem; color:#94a3b8;">💻 CPU Usage</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:#38bdf8;">{cpu}%</div>
                </div>
                <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:8px;">
                    <div style="font-size:0.75rem; color:#94a3b8;">🧠 Memory</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:#a7f3d0;">{mem}%</div>
                </div>
                <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:8px;">
                    <div style="font-size:0.75rem; color:#94a3b8;">💾 Disk</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:#fef08a;">{disk}%</div>
                </div>
                <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:8px;">
                    <div style="font-size:0.75rem; color:#94a3b8;">⏱️ Uptime</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:#e0e7ff;">{uptime}d</div>
                </div>
            </div>
        </div>
        """)

    # 3. ORDER / REFUND DATA
    elif "order_id" in data:
        o_id = data.get("order_id", "")
        cust = data.get("customer", "N/A")
        amount = data.get("amount", 0)
        eligible = data.get("refund_eligible", False)

        el_text = "YES (Eligible)" if eligible else "NO (Ineligible)"
        el_bg = "#10b981" if eligible else "#ef4444"

        return textwrap.dedent(f"""
        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95)); border: 1px solid rgba(245, 158, 11, 0.5); border-radius: 12px; padding: 1.25rem; margin: 0.75rem 0; box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
                <span style="font-size:1.1rem; font-weight:bold; color:#f8fafc;">📦 Order Details <code style="color:#f59e0b;">{html.escape(o_id)}</code></span>
                <span style="background:{el_bg}; color:white; padding:3px 8px; border-radius:6px; font-size:0.75rem; font-weight:bold;">REFUND: {el_text}</span>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size:0.9rem; color:#cbd5e1;">
                <div><b>👤 Customer:</b> {html.escape(cust)}</div>
                <div><b>💵 Amount:</b> ${amount}</div>
            </div>
        </div>
        """)

    # 4. GENERIC JSON CARD
    else:
        rows = "".join([f"<div><span style='color:#94a3b8;'>{k}:</span> <b style='color:#f8fafc;'>{v}</b></div>" for k, v in data.items()])
        return textwrap.dedent(f"""
        <div style="background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 10px; padding: 1rem; margin: 0.75rem 0;">
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size:0.95rem;">
                {rows}
            </div>
        </div>
        """)

def render_assistant_content(content_str: str):
    """Renders assistant message content: detects JSON and renders enriched UI cards!"""
    clean_c = content_str.replace("<|python_tag|>", "").replace("<|tool_call|>", "").strip()
    
    prefix_text = ""
    json_str = None
    if "```json" in clean_c and "```" in clean_c:
        try:
            start = clean_c.find("```json")
            prefix_text = clean_c[:start].strip()
            end = clean_c.find("```", start + 7)
            json_str = clean_c[start + 7:end].strip()
        except Exception:
            pass
    elif clean_c.startswith("{") and clean_c.endswith("}"):
        json_str = clean_c

    parsed_json = None
    if json_str:
        try:
            parsed_json = json.loads(json_str)
        except Exception:
            pass

    if prefix_text:
        st.markdown(prefix_text)

    if parsed_json and isinstance(parsed_json, dict):
        html_card = render_enriched_card(parsed_json)
        st.markdown(html_card, unsafe_allow_html=True)
    else:
        st.markdown(clean_c)

# --- HELPER FUNCTIONS FOR FASTAPI COMM ---

def api_login(username, password):
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/login",
            json={"username": username, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state["authenticated"] = True
            st.session_state["token"] = data["access_token"]
            st.session_state["user_info"] = {
                "username": data["username"],
                "full_name": data["full_name"],
                "role": data["role"]
            }
            st.success(f"Welcome back, {data['full_name']}!")
            st.rerun()
        else:
            err = response.json().get("detail", "Login failed")
            st.error(f"Authentication Failed: {err}")
    except Exception as e:
        st.error(f"Failed to connect to FastAPI service at {FASTAPI_BASE_URL}: {e}")

def api_send_chat(message):
    token = st.session_state["token"]
    session_id = st.session_state["session_id"]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/chat",
            json={"session_id": session_id, "message": message},
            headers=headers,
            timeout=15
        )
        if response.status_code == 200:
            res_data = response.json()
            st.session_state["pending_approval"] = res_data.get("pending_approval")
            st.session_state["current_status"] = res_data.get("status", "completed")
            st.session_state["node_history"] = res_data.get("node_history", [])
            return res_data
        elif response.status_code == 401:
            st.error("Session expired. Please log in again.")
            st.session_state["authenticated"] = False
            st.rerun()
        else:
            err = response.json().get("detail", "Error processing message")
            st.error(f"API Error: {err}")
            return None
    except Exception as e:
        st.error(f"Failed to connect to FastAPI server: {e}")
        return None

def api_send_approval(action, target_session_id=None):
    token = st.session_state["token"]
    session_id = target_session_id or st.session_state["session_id"]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/approve",
            json={"session_id": session_id, "action": action},
            headers=headers,
            timeout=15
        )
        if response.status_code == 200:
            res_data = response.json()
            if session_id == st.session_state["session_id"]:
                st.session_state["pending_approval"] = None
                st.session_state["current_status"] = res_data.get("status", "completed")
                st.session_state["node_history"] = res_data.get("node_history", [])
            return res_data
        elif response.status_code == 403:
            err = response.json().get("detail", "Access Forbidden")
            st.error(f"🚫 {err}")
            return None
        else:
            err = response.json().get("detail", "Approval failed")
            st.error(f"Approval Error: {err}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

def api_get_session_status(session_id=None):
    token = st.session_state.get("token")
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    sid = session_id or st.session_state.get("session_id")
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/status/{sid}", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def api_get_all_pending_approvals():
    token = st.session_state.get("token")
    if not token:
        return []
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/pending_approvals", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

def api_get_user_workflow_history():
    token = st.session_state.get("token")
    if not token:
        return []
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/user_workflow_history", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

# --- SMART GATED AUTO-POLLING FRAGMENT ---

@st.fragment(run_every=3)
def live_status_auto_poller():
    """Smart Gated Poller: ONLY polls FastAPI when a session is actively awaiting an approval decision!
    Saves API call overhead during idle, completed, or rejected session states.
    """
    if not st.session_state.get("authenticated"):
        return

    # Guard: Only poll if the current session has an active pending approval waiting for approver decision
    if st.session_state.get("current_status") != "awaiting_approval" and not st.session_state.get("pending_approval"):
        return

    sid = st.session_state.get("session_id")
    current_status = st.session_state.get("current_status")

    status_info = api_get_session_status(sid)
    if status_info and status_info.get("status") != "not_found":
        srv_status = status_info.get("status")
        srv_pending = status_info.get("pending_approval")
        srv_response = status_info.get("last_response")
        srv_history = status_info.get("node_history", [])

        if srv_status != current_status or srv_pending != st.session_state.get("pending_approval"):
            st.session_state["current_status"] = srv_status
            st.session_state["pending_approval"] = srv_pending
            st.session_state["node_history"] = srv_history
            
            if srv_response:
                msgs = st.session_state.get("messages", [])
                clean_res = srv_response.replace("<|python_tag|>", "").replace("<|tool_call|>", "").strip()
                if not msgs or msgs[-1].get("content") != clean_res:
                    st.session_state["messages"].append({"role": "assistant", "content": clean_res})
            st.rerun(scope="app")

# --- EVENT-DRIVEN FRAGMENT FOR APPROVER PENDING QUEUE (SIDEBAR) ---

@st.fragment
def render_live_pending_approvals_sidebar():
    st.markdown("---")
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.subheader("🚨 Pending Approvals")
    with col_h2:
        if st.button("🔄", key="ref_side_btn", help="Refresh Approvals Queue"):
            st.rerun(scope="app")

    pending_all = api_get_all_pending_approvals()
    if pending_all:
        st.caption(f"⚡ {len(pending_all)} pending approval(s):")
        for item in pending_all:
            p_sid = item["session_id"]
            p_user = item.get("username", "user")
            p_info = item["pending_approval"]
            with st.expander(f"User: {p_user} (Session {p_sid})", expanded=True):
                st.markdown(f"**Action:** `{p_info['tool_name']}`")
                st.markdown(f"**Args:** `{json.dumps(p_info['arguments'])}`")
                col_a, col_r = st.columns(2)
                with col_a:
                    if st.button("✅ Approve", key=f"app_{p_sid}", type="primary", use_container_width=True):
                        res = api_send_approval("approve", target_session_id=p_sid)
                        if res:
                            st.success(f"Approved session {p_sid}!")
                        st.rerun(scope="app")
                with col_r:
                    if st.button("🛑 Reject", key=f"rej_{p_sid}", type="secondary", use_container_width=True):
                        res = api_send_approval("reject", target_session_id=p_sid)
                        if res:
                            st.warning(f"Rejected session {p_sid}!")
                        st.rerun(scope="app")
    else:
        st.caption("No pending approvals in queue.")

# --- EVENT-DRIVEN FRAGMENT FOR USER WORKFLOW HISTORY AUDIT PANEL ---

@st.fragment
def render_live_workflow_history_panel():
    with st.expander("📜 All User Sessions & Graph Workflow Trajectory History", expanded=True):
        col_h1, col_h2 = st.columns([4, 1])
        with col_h1:
            st.markdown("<h4 style='color: #38bdf8; margin:0;'>User Session Audit & Graph Execution Trajectory</h4>", unsafe_allow_html=True)
        with col_h2:
            if st.button("🔄 Sync Trajectory", key="sync_history_btn", use_container_width=True):
                st.rerun(scope="app")

        st.markdown("<br>", unsafe_allow_html=True)
        all_history = api_get_user_workflow_history()
        if all_history:
            for sess in all_history:
                sid = sess["session_id"]
                uname = sess.get("username", "user")
                s_status = sess.get("status", "unknown")
                n_hist = format_node_trajectory(sess.get("node_history", []))
                p_info = sess.get("pending_approval")
                user_msg = sess.get("last_user_message", "")
                last_by = sess.get("last_action_by")

                status_bg = "#10b981" if s_status == "completed" else ("#f59e0b" if s_status == "awaiting_approval" else ("#ef4444" if s_status == "rejected" else "#3b82f6"))

                # Determine Action Taken details
                tool_name = "N/A"
                tool_args = "{}"
                act_category = "General Operational Query"

                if p_info:
                    tool_name = p_info.get("tool_name", "N/A")
                    tool_args = json.dumps(p_info.get("arguments", {}))
                    act_category = "⚠️ Sensitive Action (HITL Pending)"
                elif "resume_execution_node" in sess.get("node_history", []) or "execute_sensitive_tool" in sess.get("node_history", []):
                    act_category = "⚡ Sensitive Action (Approved & Executed)"
                elif "mcp_executor_node" in sess.get("node_history", []) or "call_safe_tool" in sess.get("node_history", []):
                    act_category = "⚙️ Safe Tool (MCP Auto-Executed)"
                elif "rejection_node" in sess.get("node_history", []):
                    act_category = "🛑 Sensitive Action (Rejected by Approver)"

                approver_html = f'<span style="margin-left:12px; color:#cbd5e1; font-size:0.85rem;">🛡️ Approver: <b style="color:#a7f3d0;">{html.escape(last_by)}</b></span>' if last_by else ""
                user_msg_html = f'<div style="font-size:0.9rem; color:#cbd5e1; margin-bottom:0.6rem;">💬 <b>User Request:</b> <span style="color:#f8fafc; font-style:italic;">"{html.escape(user_msg)}"</span></div>' if user_msg else ""
                tool_args_html = f'<div style="grid-column: span 2;"><span style="color:#94a3b8;">📋 Tool Arguments:</span> <code style="color:#a7f3d0;">{html.escape(tool_args)}</code></div>' if tool_args != "{}" else ""

                card_html = f"""<div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(168, 85, 247, 0.35); border-radius: 12px; padding: 1.1rem; margin-bottom: 0.85rem; box-shadow: 0 4px 16px rgba(0,0,0,0.35);">
<div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.6rem; margin-bottom: 0.6rem;">
<div>
<span style="font-size:1rem; font-weight:700; color:#38bdf8;">🔑 Session: <code>{sid}</code></span>
<span style="margin-left:12px; color:#94a3b8; font-size:0.88rem;">👤 User: <b style="color:#f8fafc;">{uname}</b></span>
{approver_html}
</div>
<span style="background:{status_bg}; color:white; padding:4px 12px; border-radius:12px; font-size:0.75rem; font-weight:700;">{s_status.upper()}</span>
</div>
{user_msg_html}
<div style="background: rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 0.75rem; margin-bottom: 0.6rem;">
<div style="font-size:0.88rem; font-weight:700; color:#a7f3d0; margin-bottom: 4px;">⚡ Action Taken & Operational Details:</div>
<div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size:0.85rem;">
<div><span style="color:#94a3b8;">🛠️ Action / Tool:</span> <code style="color:#38bdf8; font-weight:bold;">{html.escape(tool_name)}</code></div>
<div><span style="color:#94a3b8;">🏷️ Category:</span> <b style="color:#f8fafc;">{act_category}</b></div>
{tool_args_html}
</div>
</div>
<div style="font-size:0.85rem; color:#cbd5e1;">
📊 <b>Graph Trajectory Path:</b> <code style="color:#a7f3d0; font-weight:bold; background:rgba(0,0,0,0.4); padding:2px 8px; border-radius:4px;">{html.escape(n_hist)}</code>
</div>
</div>"""

                st.markdown(card_html, unsafe_allow_html=True)

                if p_info:
                    col_a, col_r, _ = st.columns([1, 1, 3])
                    with col_a:
                        if st.button("✅ Approve", key=f"aud_app_{sid}", type="primary", use_container_width=True):
                            res = api_send_approval("approve", target_session_id=sid)
                            st.rerun(scope="app")
                    with col_r:
                        if st.button("🛑 Reject", key=f"aud_rej_{sid}", type="secondary", use_container_width=True):
                            res = api_send_approval("reject", target_session_id=sid)
                            st.rerun(scope="app")
        else:
            st.info("No active user workflow sessions recorded yet.")

# --- WORKFLOW GRAPH RENDERER ---

def render_workflow_graph(current_status: str, pending_info: dict = None, node_history: list = None):
    router_style = "background: #334155; color: white;"
    safe_style = "background: #334155; color: #94a3b8;"
    hitl_style = "background: #334155; color: #94a3b8;"
    sensitive_style = "background: #334155; color: #94a3b8;"
    rejection_style = "background: #334155; color: #94a3b8;"

    if current_status == "awaiting_approval":
        router_style = "background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; border: 1px solid white;"
        hitl_style = "background: linear-gradient(135deg, #ef4444, #dc2626); color: white; box-shadow: 0 0 18px #ef4444; border: 2px solid white; transform: scale(1.05);"
    elif current_status == "executing_safe":
        router_style = "background: linear-gradient(135deg, #1e40af, #3b82f6); color: white;"
        safe_style = "background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; box-shadow: 0 0 18px #3b82f6; border: 2px solid white;"
    elif current_status == "executing_sensitive" or (current_status == "completed" and pending_info is None):
        router_style = "background: linear-gradient(135deg, #1e40af, #3b82f6); color: white;"
        sensitive_style = "background: linear-gradient(135deg, #10b981, #059669); color: white; box-shadow: 0 0 18px #10b981; border: 2px solid white;"
    elif current_status == "rejected":
        router_style = "background: linear-gradient(135deg, #1e40af, #3b82f6); color: white;"
        rejection_style = "background: linear-gradient(135deg, #f59e0b, #d97706); color: white; box-shadow: 0 0 18px #f59e0b; border: 2px solid white; transform: scale(1.05);"

    history_str = format_node_trajectory(node_history or [])

    st.markdown(textwrap.dedent(f"""
        <div class="graph-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="color: #a855f7; margin:0; font-size:1.3rem;">📊 LangGraph Active Workflow State Diagram</h3>
                <span style="font-size:0.85rem; background:rgba(255,255,255,0.1); padding:4px 10px; border-radius:6px; border:1px solid rgba(255,255,255,0.2);">⚡ Workflow State | Status: <b style="color:#38bdf8;">{current_status.upper()}</b></span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-around; flex-wrap: wrap; gap: 8px; margin: 20px 0;">
                <div style="padding: 10px 14px; border-radius: 8px; background: #1e293b; color: #f8fafc; font-weight:600;">🚀 START</div>
                <div style="color: #64748b; font-weight: bold;">➔</div>
                <div style="padding: 10px 14px; border-radius: 8px; {router_style} font-weight:600;">🔀 router_node</div>
                <div style="color: #64748b; font-weight: bold;">➔</div>
                <div style="padding: 10px 14px; border-radius: 8px; {safe_style} font-weight:600;">⚙️ mcp_executor_node</div>
                <div style="color: #64748b; font-weight: bold;">➔</div>
                <div style="padding: 10px 14px; border-radius: 8px; {hitl_style} font-weight:600;">⚠️ approval_node (Interrupt)</div>
                <div style="color: #64748b; font-weight: bold;">➔</div>
                <div style="padding: 10px 14px; border-radius: 8px; {sensitive_style} font-weight:600;">⚡ resume_execution_node</div>
                <div style="color: #64748b; font-weight: bold;">/</div>
                <div style="padding: 10px 14px; border-radius: 8px; {rejection_style} font-weight:600;">🛑 rejection_node</div>
            </div>
            <div style="font-size: 1.05rem; color: #f8fafc; background: rgba(0,0,0,0.4); padding:10px 14px; border-radius:8px; border: 1px solid rgba(168, 85, 247, 0.4);">
                <b>📜 Graph Execution Path History:</b> <code style="color: #a7f3d0; font-size: 1.15rem; font-weight: bold;">{history_str}</code>
            </div>
        </div>
    """), unsafe_allow_html=True)

# --- UI VIEW 1: LOGIN PAGE ---

if not st.session_state["authenticated"]:
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 3rem; background: linear-gradient(90deg, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                ⚡ Agentic Ops Assistant
            </h1>
            <p style="color: #94a3b8; font-size: 1.1rem;">Enterprise Operations Management powered by MCP & LangGraph</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='user-card'>", unsafe_allow_html=True)
        st.subheader("🔑 Sign In to Operations Portal")
        
        with st.form("login_form"):
            username = st.text_input("Username", value="")
            password = st.text_input("Password", type="password", value="")
            submit = st.form_submit_button("Log In", use_container_width=True)

            if submit:
                api_login(username, password)
        
        st.markdown("</div>", unsafe_allow_html=True)

# --- UI VIEW 2: MAIN DASHBOARD & CHAT ---

else:
    # Run Background Real-Time Auto Poller
    live_status_auto_poller()

    user_info = st.session_state["user_info"]
    role_badge = (
        "<span class='badge-approver'>Approver</span>"
        if user_info["role"] == "approver"
        else "<span class='badge-user'>User</span>"
    )

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("<div class='user-card'>", unsafe_allow_html=True)
        st.markdown(f"### 👤 {user_info['full_name']}")
        st.markdown(f"**Username:** `{user_info['username']}`")
        st.markdown(f"**Role:** {role_badge}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"**Current Session:** `{st.session_state['session_id']}`")
        if st.button("➕ New Chat Session", use_container_width=True):
            st.session_state["session_id"] = str(uuid.uuid4())[:8]
            st.session_state["messages"] = []
            st.session_state["pending_approval"] = None
            st.session_state["current_status"] = "idle"
            st.session_state["node_history"] = []
            st.rerun()

        # APPROVER GLOBAL PENDING QUEUE (Auto-Refreshed Live Fragment!)
        if user_info["role"] == "approver":
            render_live_pending_approvals_sidebar()

        st.markdown("---")
        if st.button("🚪 Log Out", type="secondary", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["token"] = ""
            st.session_state["messages"] = []
            st.rerun()

    # --- MAIN HEADER ---
    st.markdown("""
        <div class='main-header'>
            <h2 style='margin:0; font-size:1.8rem;'>⚡ Agentic Ops Assistant Dashboard</h2>
            <p style='margin:5px 0 0 0; opacity:0.9;'>Orchestrating Ops Business Logic via MCP Server & LangGraph HITL</p>
        </div>
    """, unsafe_allow_html=True)

    # --- APPROVER ROLE: USER WORKFLOW HISTORY AUDIT PANEL (Auto-Refreshed Live Fragment!) ---
    if user_info["role"] == "approver":
        render_live_workflow_history_panel()

    # --- WORKFLOW GRAPH DIAGRAM DISPLAY ---
    render_workflow_graph(
        st.session_state["current_status"],
        st.session_state["pending_approval"],
        st.session_state.get("node_history")
    )

    # --- PENDING APPROVAL DISPLAY (ROLE BASED) ---
    pending = st.session_state["pending_approval"]
    if pending:
        if user_info["role"] == "approver":
            st.markdown("<div class='approval-box'>", unsafe_allow_html=True)
            st.markdown("### ⚠️ Approval Decision Required")
            st.markdown(f"**Action:** `{pending.get('tool_name')}`")
            st.markdown(f"**Arguments:** `{json.dumps(pending.get('arguments', {}))}`")
            st.markdown(f"*{pending.get('description', 'Sensitive operational action requires authorized confirmation.')}*")

            col_app, col_rej, _ = st.columns([1, 1, 2])
            with col_app:
                if st.button("✅ Approve & Execute", type="primary", use_container_width=True):
                    res = api_send_approval("approve")
                    if res and res.get("response"):
                        st.session_state["messages"].append({"role": "assistant", "content": res["response"]})
                        st.rerun(scope="app")

            with col_rej:
                if st.button("🛑 Reject Action", type="secondary", use_container_width=True):
                    res = api_send_approval("reject")
                    if res and res.get("response"):
                        st.session_state["messages"].append({"role": "assistant", "content": res["response"]})
                        st.rerun(scope="app")

            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(textwrap.dedent(f"""
            <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.35) 100%); border: 2px solid #3b82f6; border-radius: 12px; padding: 1.5rem; margin: 1.5rem 0; box-shadow: 0 0 25px rgba(59, 130, 246, 0.4);">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid rgba(255,255,255,0.15); padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
                    <span style="font-size:1.25rem; font-weight:700; color:#60a5fa;">📩 Request Sent for Approval</span>
                    <span style="background:#f59e0b; color:white; padding:4px 12px; border-radius:12px; font-size:0.8rem; font-weight:700;">⏳ Pending Approval</span>
                </div>
                <div style="font-size:0.95rem; line-height: 1.6;">
                    <div style="margin-bottom:6px;"><span style="color:#94a3b8;">🛠️ Action Requested:</span> <code style="color:#f8fafc; font-size:1rem; font-weight:bold;">{pending.get('tool_name')}</code></div>
                    <div style="margin-bottom:6px;"><span style="color:#94a3b8;">📋 Details / Arguments:</span> <code style="color:#a7f3d0; font-weight:bold;">{json.dumps(pending.get('arguments', {}))}</code></div>
                    <div style="margin-top:0.5rem; color:#cbd5e1;"><i>{pending.get('description', 'Sensitive operational action requires authorized confirmation from lead/approver.')}</i></div>
                </div>
                <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid rgba(255,255,255,0.1); font-size:0.85rem; color:#93c5fd; display:flex; align-items:center;">
                    <span class="live-pulse"></span> <span>Your request has been sent for approval. Status and final details will update automatically here once approved or rejected.</span>
                </div>
            </div>
            """), unsafe_allow_html=True)

    # --- CHAT HISTORY CONTAINER ---
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state["messages"]:
            raw_c = msg.get("content", "")
            clean_c = raw_c.replace("<|python_tag|>", "").replace("<|tool_call|>", "").strip()
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-bubble-user'><b>👤 You:</b><br>{html.escape(clean_c)}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='chat-bubble-ai'><b>🤖 Ops Assistant:</b></div>", unsafe_allow_html=True)
                render_assistant_content(clean_c)

    # --- CHAT INPUT FORM ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #38bdf8; font-weight: 700; margin-bottom: 5px;'>💬 Ask a question or request an action...</h3>", unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Enter your operational query or command below:",
            placeholder="e.g. Process refund for ORD-5003 amount 14 or Restart server auth-prod-01"
        )
        send_btn = st.form_submit_button("Send Message 🚀", use_container_width=True)

        if send_btn and user_input.strip():
            st.session_state["messages"].append({"role": "user", "content": user_input})
            res = api_send_chat(user_input)
            if res and res.get("response"):
                st.session_state["messages"].append({"role": "assistant", "content": res["response"]})
            st.rerun()
