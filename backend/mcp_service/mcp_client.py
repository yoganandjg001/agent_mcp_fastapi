import asyncio
import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment configuration
load_dotenv()

class MCPClient:
    def __init__(self, server_url: Optional[str] = None):
        self.mcp_server_url = server_url or os.getenv("MCP_SERVER_URL", "http://localhost:8001/sse")

        # Initialize MultiServerMCPClient using SSE connection configuration
        self.multi_client = MultiServerMCPClient(
            {
                "MCP_Server": {
                    "url": self.mcp_server_url,
                    "transport": "sse"
                }
            }
        )

    async def _execute_async(self, action: str, tool_name: str = "", tool_args: Optional[Dict[str, Any]] = None) -> Any:
        tool_args = tool_args or {}

        if action == "list_tools":
            tools = await self.multi_client.get_tools()
            tool_list = []
            for t in tools:
                tool_list.append({
                    "name": t.name,
                    "description": t.description,
                    "input_schema": getattr(t, "args_schema", {}) or {}
                })
            return tool_list
        elif action == "call_tool":
            async with self.multi_client.session("MCP_Server") as session:
                result = await session.call_tool(tool_name, tool_args)
                if result.content and len(result.content) > 0:
                    return result.content[0].text
                return json.dumps({"status": "empty response"})
        else:
            raise ValueError(f"Unknown action: {action}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Synchronously list available tools from MCP Server."""
        return asyncio.run(self._execute_async("list_tools"))

    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """Synchronously invoke an MCP tool on the MCP Server via MCP protocol."""
        return asyncio.run(self._execute_async("call_tool", tool_name=tool_name, tool_args=arguments or {}))

    async def call_tool_async(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """Asynchronously invoke an MCP tool on the MCP Server via MCP protocol."""
        return await self._execute_async("call_tool", tool_name=tool_name, tool_args=arguments or {})

# Global singleton client instance
mcp_client = MCPClient()
