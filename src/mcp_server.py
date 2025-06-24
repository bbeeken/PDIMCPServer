"""MCP PDI Server - Main server implementation"""

from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent

from .tool_list import TOOLS


def create_server() -> Server:
    """Create and configure the MCP server"""
    server = Server("mcp-pdi-sales")

    tools: List[Tool] = TOOLS

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]):
        tool_map = {t.name: t for t in tools}
        if name not in tool_map:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        tool = tool_map[name]
        if not hasattr(tool, "_implementation"):
            return [TextContent(type="text", text=f"Tool {name} has no implementation")]

        try:
            result = await tool._implementation(**arguments)
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                import json

                return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            return [TextContent(type="text", text=str(result))]
        except Exception as exc:
            return [TextContent(type="text", text=str(exc))]

    server.tools = tools
    return server


async def run_server():
    """Run the MCP server"""
    server = create_server()
    await server.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_server())
