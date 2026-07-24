import json
import os
import sys
import datetime

from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv


# Load environment configuration without overriding process environment variables
load_dotenv(override=False)


# Initialize FastMCP Server
mcp = FastMCP("AgenticOpsServer")


# Path helper for data files (pointing to project root/data)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def _read_json(filename: str) -> List[Dict[str, Any]]:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        # Fallback to uploaded dir if needed
        path = os.path.join(BASE_DIR, "uploaded", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(filename: str, data: List[Dict[str, Any]]):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# --- MCP TOOLS ---

@mcp.tool()
def check_server_health(server_name: Optional[str] = None) -> str:
    """Check the operational health, CPU, memory, and status of servers.
    If server_name is provided, returns details for that specific server.
    Otherwise returns a summary of all servers.
    """
    servers = _read_json("servers.json")
    if server_name:
        for s in servers:
            if s["server_name"].lower() == server_name.lower():
                return json.dumps(s, indent=2)
        return json.dumps({"error": f"Server '{server_name}' not found."})
    return json.dumps(servers, indent=2)

@mcp.tool()
def get_ticket_status(ticket_id: Optional[str] = None) -> str:
    """Retrieve ticket status, priority, and assignment info.
    If ticket_id is provided, returns details for that ticket.
    Otherwise returns a list of all tickets.
    """
    tickets = _read_json("tickets.json")
    if ticket_id:
        for t in tickets:
            if t["ticket_id"].lower() == ticket_id.lower():
                return json.dumps(t, indent=2)
        return json.dumps({"error": f"Ticket '{ticket_id}' not found."})
    return json.dumps(tickets, indent=2)

@mcp.tool()
def calculate_refund(order_id: str, amount: Optional[float] = None) -> str:
    """Calculate refund eligibility and total returnable amount for an order."""
    orders = _read_json("orders.json")
    for o in orders:
        if o["order_id"].lower() == order_id.lower():
            order_amount = o["order_amount"]
            eligible = o.get("refund_eligible", False)
            requested_amount = amount if amount is not None else order_amount
            if not eligible:
                return json.dumps({
                    "order_id": o["order_id"],
                    "customer": o["customer"],
                    "status": "Ineligible",
                    "reason": "Order return window passed or item non-refundable",
                    "refund_amount": 0.0
                })
            actual_refund = min(requested_amount, order_amount)
            return json.dumps({
                "order_id": o["order_id"],
                "customer": o["customer"],
                "product": o["product"],
                "order_amount": order_amount,
                "requested_amount": requested_amount,
                "calculated_refund": actual_refund,
                "status": "Eligible for refund"
            })
    return json.dumps({"error": f"Order '{order_id}' not found."})

@mcp.tool()
def restart_server(server_name: str) -> str:
    """[SENSITIVE ACTION] Restart a server by name, updating status to healthy and resetting CPU/memory metrics."""
    servers = _read_json("servers.json")
    found = False
    for s in servers:
        if s["server_name"].lower() == server_name.lower():
            s["status"] = "healthy"
            s["cpu_percent"] = 15
            s["memory_percent"] = 25
            s["uptime_days"] = 0
            s["last_restart"] = datetime.date.today().isoformat()
            found = True
            break
    if found:
        _write_json("servers.json", servers)
        return json.dumps({"status": "Success", "message": f"Server '{server_name}' restarted successfully."})
    return json.dumps({"error": f"Server '{server_name}' not found."})

@mcp.tool()
def process_refund(order_id: str, amount: float) -> str:
    """[SENSITIVE ACTION] Issue a financial refund for an order."""
    orders = _read_json("orders.json")
    found = False
    for o in orders:
        if o["order_id"].lower() == order_id.lower():
            if not o.get("refund_eligible", False):
                return json.dumps({"error": f"Order '{order_id}' is not eligible for a refund."})
            o["refund_eligible"] = False
            found = True
            break
    if found:
        _write_json("orders.json", orders)
        return json.dumps({
            "status": "Success",
            "message": f"Refund of ${amount:.2f} processed successfully for order '{order_id}'."
        })
    return json.dumps({"error": f"Order '{order_id}' not found."})

@mcp.tool()
def escalate_ticket(ticket_id: str, priority: str = "critical") -> str:
    """[SENSITIVE ACTION] Escalate a support ticket priority and reassign to senior IT level."""
    tickets = _read_json("tickets.json")
    found = False
    for t in tickets:
        if t["ticket_id"].lower() == ticket_id.lower():
            t["priority"] = priority
            t["assigned_to"] = "IT-L3"
            t["status"] = "in_progress"
            found = True
            break
    if found:
        _write_json("tickets.json", tickets)
        return json.dumps({
            "status": "Success",
            "message": f"Ticket '{ticket_id}' escalated to priority '{priority}' and assigned to IT-L3."
        })
    return json.dumps({"error": f"Ticket '{ticket_id}' not found."})

@mcp.tool()
def validate_user_login(username: str, password: str) -> str:
    """Validate user credentials against the user directory and return user role."""
    users = _read_json("users.json")
    for u in users:
        if u["username"].lower() == username.lower() and u["password"] == password:
            return json.dumps({
                "valid": True,
                "username": u["username"],
                "full_name": u["full_name"],
                "role": u["role"]
            })
    return json.dumps({"valid": False, "error": "Invalid username or password"})

if __name__ == "__main__":
    if "--stdio" in sys.argv:
        mcp.run(transport="stdio")
    else:
        transport = os.getenv("MCP_TRANSPORT", "sse")
        port = int(os.getenv("MCP_PORT", "8001"))
        host = os.getenv("MCP_HOST", "0.0.0.0")

        if transport.lower() == "sse":
            mcp.settings.host = host
            mcp.settings.port = port
            print("==================================================")
            print(f"🚀 Starting Standalone MCP Server (SSE) on http://{host}:{port}/sse")
            print("==================================================")
            mcp.run(transport="sse")
        else:
            mcp.run(transport="stdio")


