"""FastAPI server exposing MCP tools as HTTP endpoints."""
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .tools.sales.query_realtime import query_sales_realtime_tool
from .tools.sales.sales_summary import sales_summary_tool
from .tools.sales.sales_trend import sales_trend_tool
from .tools.sales.top_items import top_items_tool
from .tools.basket.basket_analysis import basket_analysis_tool
from .tools.basket.item_correlation import item_correlation_tool
from .tools.basket.basket_metrics import basket_metrics_tool
from .tools.basket.cross_sell import cross_sell_opportunities_tool
from .tools.analytics.hourly_sales import hourly_sales_tool
from .tools.analytics.peak_hours import peak_hours_tool
from .tools.analytics.product_velocity import product_velocity_tool
from .tools.analytics.sales_anomalies import sales_anomalies_tool


def create_app() -> FastAPI:
    """Create the FastAPI application with tool routes."""
    app = FastAPI(title="mcp-pdi-sales", version="1.0.0")

    tools = [
        query_sales_realtime_tool,
        sales_summary_tool,
        sales_trend_tool,
        top_items_tool,
        basket_analysis_tool,
        item_correlation_tool,
        basket_metrics_tool,
        cross_sell_opportunities_tool,
        hourly_sales_tool,
        peak_hours_tool,
        product_velocity_tool,
        sales_anomalies_tool,
    ]

    tool_map = {t.name: t for t in tools}

    class CallRequest(BaseModel):
        tool: str
        arguments: Dict[str, Any] = {}

    @app.get("/tools")
    async def list_tools() -> List[Dict[str, Any]]:
        """Return metadata for all available tools."""
        return [
            {
                "name": t.name,
                "description": getattr(t, "description", ""),
                "inputSchema": getattr(t, "inputSchema", {}),
            }
            for t in tools
        ]

    @app.post("/call")
    async def call_tool(req: CallRequest) -> Any:
        """Execute the given tool with provided arguments."""
        if req.tool not in tool_map:
            raise HTTPException(status_code=404, detail=f"Unknown tool {req.tool}")

        tool = tool_map[req.tool]
        if not hasattr(tool, "_implementation"):
            raise HTTPException(
                status_code=500,
                detail=f"Tool {req.tool} has no implementation",
            )

        result = await tool._implementation(**req.arguments)
        return result

    return app


app = create_app()

