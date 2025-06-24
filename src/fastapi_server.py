"""FastAPI wrapper exposing MCP tools with SSE support."""

import logging
import os
from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException
from fastapi_mcp import FastApiMCP
from mcp.types import Tool

from .tool_list import TOOLS

logger = logging.getLogger(__name__)

SERVER_NAME = os.getenv("MCP_SERVER_NAME", "mcp-pdi-sales")
SERVER_VERSION = os.getenv("MCP_SERVER_VERSION", "1.0.0")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title=SERVER_NAME, version=SERVER_VERSION)

    # Create one endpoint per tool so FastApiMCP can expose them as MCP tools
    for tool in TOOLS:
        schema = tool.inputSchema if isinstance(tool.inputSchema, dict) else {}

        def make_endpoint(t: Tool):
            async def endpoint(data: Dict[str, Any] = Body(..., json_schema_extra=schema)):
                if not hasattr(t, "_implementation"):
                    raise HTTPException(
                        status_code=500, detail=f"Tool {t.name} has no implementation"
                    )
                return await t._implementation(**data)

            return endpoint

        app.post(f"/{tool.name}", operation_id=tool.name)(make_endpoint(tool))

    # Simple listing endpoint for convenience
    @app.get("/tools")
    async def list_tools() -> List[Tool]:
        return TOOLS

    # Mount the MCP SSE interface and expose the underlying MCP server
    mcp = FastApiMCP(app)
    mcp.mount()
    app.state.mcp = mcp

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
