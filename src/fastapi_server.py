"""FastAPI wrapper exposing MCP tools as HTTP endpoints."""

import logging
import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from mcp.types import Tool, TextContent

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
from .tools.item_lookup import item_lookup_tool
from .tools.site_lookup import site_lookup_tool
from .tools.get_today_date import get_today_date_tool

logger = logging.getLogger(__name__)

SERVER_NAME = os.getenv("MCP_SERVER_NAME", "mcp-pdi-sales")
SERVER_VERSION = os.getenv("MCP_SERVER_VERSION", "1.0.0")

TOOLS: List[Tool] = [
    query_sales_realtime_tool,
    sales_summary_tool,
    sales_trend_tool,
    top_items_tool,
    basket_analysis_tool,
    item_correlation_tool,
    cross_sell_opportunities_tool,
    hourly_sales_tool,
    sales_gaps_tool,
    year_over_year_tool,
    item_lookup_tool,
    site_lookup_tool,
    get_today_date_tool,
]

tool_map = {t.name: t for t in TOOLS}


class CallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title=SERVER_NAME, version=SERVER_VERSION)

    @app.get("/tools", response_model=None)
    async def list_tools() -> List[Tool]:
        logger.debug("Listing %d tools", len(TOOLS))
        return TOOLS

    @app.post("/call", response_model=None)
    async def call_tool(req: CallRequest) -> List[TextContent]:
        if req.name not in tool_map:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {req.name}")
        tool = tool_map[req.name]
        if not hasattr(tool, "_implementation"):
            raise HTTPException(
                status_code=500, detail=f"Tool {req.name} has no implementation"
            )
        try:
            result = await tool._implementation(**req.arguments)
            if isinstance(result, dict):
                import json

                formatted = json.dumps(result, indent=2, default=str)
            else:
                formatted = str(result)
            return [TextContent(type="text", text=formatted)]
        except Exception as exc:  # pragma: no cover - safety net
            logger.exception("Error executing %s", req.name)
            raise HTTPException(status_code=500, detail=str(exc))

    return app


def main() -> None:
    """Run the FastAPI server using uvicorn."""
    import uvicorn

    uvicorn.run(
        "src.fastapi_server:create_app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    main()
