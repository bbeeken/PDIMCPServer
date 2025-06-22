
"""FastAPI wrapper exposing MCP tools as HTTP endpoints."""

import logging
import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException


"""FastAPI server exposing MCP tools."""
import os
import logging
from typing import Any, Dict, List

from fastapi import FastAPI

from pydantic import BaseModel

from mcp.types import Tool, TextContent



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

from .tools.basket.cross_sell import cross_sell_opportunities_tool

logger = logging.getLogger(__name__)

SERVER_NAME = os.getenv("MCP_SERVER_NAME", "mcp-pdi-sales")
SERVER_VERSION = os.getenv("MCP_SERVER_VERSION", "1.0.0")


# Shared list of tools
TOOLS: List[Tool] = [
    query_sales_realtime_tool,
    sales_summary_tool,
    sales_trend_tool,
    top_items_tool,
    basket_analysis_tool,
    item_correlation_tool,
    cross_sell_opportunities_tool,
]

tool_map = {tool.name: tool for tool in TOOLS}

class CallRequest(BaseModel):
    """Request model for /call endpoint."""

    name: str
    arguments: Dict[str, Any] = {}


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(title=SERVER_NAME, version=SERVER_VERSION)

    @app.get("/tools", response_model=List[Tool])
    async def list_tools() -> List[Tool]:
        """Return the available tools."""
        logger.debug("Listing %d tools", len(TOOLS))
        return TOOLS

    @app.post("/call", response_model=List[TextContent])
    async def call_tool(req: CallRequest) -> List[TextContent]:
        """Execute the specified tool and return its results."""
        if req.name not in tool_map:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {req.name}")

        tool = tool_map[req.name]
        if not hasattr(tool, "_implementation"):
            raise HTTPException(status_code=500, detail=f"Tool {req.name} has no implementation")

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


def create_app() -> FastAPI:
    """Create FastAPI application with tool routes."""
    app = FastAPI(title=SERVER_NAME, version=SERVER_VERSION)

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

app = create_app()

if __name__ == "__main__":  # pragma: no cover - manual start
    import uvicorn

    uvicorn.run("src.fastapi_server:app", host="0.0.0.0", port=8000)


