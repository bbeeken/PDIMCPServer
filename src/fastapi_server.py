"""FastAPI server exposing MCP tools."""
import os
import logging
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

from mcp.types import Tool, TextContent

from .tools.sales.query_realtime import query_sales_realtime_tool
from .tools.sales.sales_summary import sales_summary_tool
from .tools.sales.sales_trend import sales_trend_tool
from .tools.sales.top_items import top_items_tool
from .tools.basket.basket_analysis import basket_analysis_tool
from .tools.basket.item_correlation import item_correlation_tool
from .tools.basket.cross_sell import cross_sell_opportunities_tool

logger = logging.getLogger(__name__)

SERVER_NAME = os.getenv("MCP_SERVER_NAME", "mcp-pdi-sales")
SERVER_VERSION = os.getenv("MCP_SERVER_VERSION", "1.0.0")


def create_app() -> FastAPI:
    """Create FastAPI application with tool routes."""
    app = FastAPI(title=SERVER_NAME, version=SERVER_VERSION)

    tools = [
        query_sales_realtime_tool,
        sales_summary_tool,
        sales_trend_tool,
        top_items_tool,
        basket_analysis_tool,
        item_correlation_tool,
        cross_sell_opportunities_tool,
    ]
    tool_map = {t.name: t for t in tools}

    @app.get("/tools")
    async def list_tools() -> List[Dict[str, Any]]:
        """Return all available tools."""
        logger.debug("Listing %d tools", len(tools))
        cleaned = []
        for t in tools:
            cleaned.append({
                "name": getattr(t, "name", ""),
                "description": getattr(t, "description", ""),
                "inputSchema": getattr(t, "inputSchema", {}),
            })
        return cleaned

    class CallRequest(BaseModel):
        name: str
        arguments: Dict[str, Any] = {}

    @app.post("/call")
    async def call_tool(request: CallRequest) -> List[Dict[str, Any]]:
        """Execute a tool by name."""
        name = request.name
        arguments = request.arguments
        logger.info("Calling tool %s with args %s", name, arguments)

        if name not in tool_map:
            error_msg = f"Unknown tool: {name}"
            logger.error(error_msg)
            return [{"type": "text", "text": error_msg}]

        tool = tool_map[name]
        if not hasattr(tool, "_implementation"):
            error_msg = f"Tool {name} has no implementation"
            logger.error(error_msg)
            return [{"type": "text", "text": error_msg}]

        try:
            result = await tool._implementation(**arguments)
            if isinstance(result, dict):
                import json
                formatted = json.dumps(result, indent=2, default=str)
            else:
                formatted = str(result)
            return [{"type": "text", "text": formatted}]
        except Exception as e:  # pragma: no cover - defensive
            error_msg = f"Error executing {name}: {e}"
            logger.error(error_msg, exc_info=True)
            return [{"type": "text", "text": error_msg}]

    return app


app = create_app()

if __name__ == "__main__":  # pragma: no cover - manual start
    import uvicorn

    uvicorn.run("src.fastapi_server:app", host="0.0.0.0", port=8000)
