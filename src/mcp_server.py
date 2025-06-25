"""MCP PDI Server - Main server implementation."""

from typing import Any, Dict, List


from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tool_list import TOOLS

from mcp.server import Server
from mcp.types import Tool, TextContent

# Import all tools
from .tools.sales.query_realtime import query_sales_realtime_tool
from .tools.sales.sales_summary import sales_summary_tool
from .tools.sales.sales_trend import sales_trend_tool
from .tools.sales.top_items import top_items_tool
from .tools.basket.basket_analysis import basket_analysis_tool
from .tools.basket.item_correlation import item_correlation_tool
from .tools.basket.cross_sell import cross_sell_opportunities_tool
from .tools.analytics.hourly_sales import hourly_sales_tool
from .tools.analytics.sales_gaps import sales_gaps_tool
from .tools.analytics.year_over_year import year_over_year_tool
from .tools.site_lookup import site_lookup_tool
from .tools.item_lookup import item_lookup_tool
from .tools.get_today_date import get_today_date_tool



def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("mcp-pdi-sales")

    tools: List[Tool] = TOOLS
    server.tools = tools


    tools: List[Tool] = [
        # Sales tools
        query_sales_realtime_tool,
        sales_summary_tool,
        sales_trend_tool,
        top_items_tool,
        # Basket analysis
        basket_analysis_tool,
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

                return [
                    TextContent(
                        type="text", text=json.dumps(result, indent=2, default=str)
                    )
                ]
            return [TextContent(type="text", text=str(result))]

        except Exception as exc:  # pragma: no cover - pass errors through
            return [TextContent(type="text", text=str(exc))]

    return server


async def run_server() -> None:
    """Run the MCP server over STDIO."""

        except Exception as exc:  # pragma: no cover - safety net
            return [TextContent(type="text", text=str(exc))]

    server.tools = tools
    return server


async def run_server():
    """Run the MCP server."""

    server = create_server()
    await server.run()

if __name__ == "__main__":  # pragma: no cover - manual run
    import asyncio

    asyncio.run(run_server())
