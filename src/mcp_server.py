"""MCP server that reuses the FastAPI MCP instance for stdio."""

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .fastapi_server import create_app
    """Return the MCP server used by the FastAPI app."""
    app: FastAPI = create_app()
    mcp: FastApiMCP = app.state.mcp
    server = mcp.server
    # Expose tool list for convenience
    server.tools = mcp.tools
    """Run the MCP server over STDIO."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )
        item_correlation_tool,
        cross_sell_opportunities_tool,
        # Analytics
        hourly_sales_tool,
        sales_gaps_tool,
        year_over_year_tool,
        # Utility tools
        item_lookup_tool,
        site_lookup_tool,
        get_today_date_tool,
    ]


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
