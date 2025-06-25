"""FastAPI wrapper exposing MCP tools with SSE support."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException
from fastapi_mcp import FastApiMCP
from mcp.types import Tool

from . import __version__

from .mcp_server import create_server


logger = logging.getLogger(__name__)

SERVER_NAME = os.getenv("MCP_SERVER_NAME", "mcp-pdi-sales")
SERVER_VERSION = os.getenv("MCP_SERVER_VERSION", __version__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=SERVER_NAME,
        version=SERVER_VERSION,
        description="All endpoints reject unknown parameters with a 422 error.",
    )

    server = create_server()

    # Create one endpoint per tool so FastApiMCP can expose them as MCP tools
    for tool in server.tools:
        schema = tool.inputSchema if isinstance(tool.inputSchema, dict) else {}

        def build_example(spec: Dict[str, Any]) -> Dict[str, Any]:
            example = {}
            for name, prop in spec.get("properties", {}).items():
                if "default" in prop:
                    example[name] = prop["default"]
                else:
                    t = prop.get("type")
                    if t == "integer":
                        example[name] = 0
                    elif t == "array":
                        example[name] = []
                    elif t == "boolean":
                        example[name] = False
                    else:
                        example[name] = ""
            return example

        openapi_schema = dict(schema)
        openapi_schema["example"] = build_example(schema)

        def make_endpoint(t: Tool) -> Any:
            async def endpoint(
                data: Dict[str, Any] = Body(..., json_schema_extra=openapi_schema)
            ) -> Any:
                if not hasattr(t, "_implementation"):
                    raise HTTPException(
                        status_code=500,
                        detail=f"Tool {t.name} has no implementation",
                    )

                allowed = set(schema.get("properties", {}))
                extra_keys = set(data) - allowed
                if extra_keys:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Unknown parameters: {', '.join(sorted(extra_keys))}",
                    )

                filtered_data = {k: v for k, v in data.items() if k in allowed}
                return await t._implementation(**filtered_data)

            return endpoint

        app.post(f"/{tool.name}", operation_id=tool.name)(make_endpoint(tool))

    @app.get("/tools")
    async def list_tools() -> List[Tool]:
        return server.tools

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


if __name__ == "__main__":  # pragma: no cover - manual run
    main()
