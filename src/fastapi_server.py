"""FastAPI wrapper exposing MCP tools with SSE support."""

import logging
import os
from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException
from fastapi_mcp import FastApiMCP
from mcp.types import Tool


        async def endpoint(
            data: Dict[str, Any] = Body(..., json_schema_extra=schema),
            _tool=tool,
        ) -> Any:
            if not hasattr(_tool, "_implementation"):
                raise HTTPException(
                    status_code=500,
                    detail=f"Tool {_tool.name} has no implementation",
                )

            return await _tool._implementation(**data)

        app.post(f"/{tool.name}", operation_id=tool.name)(endpoint)

    app = FastAPI(title=SERVER_NAME, version=SERVER_VERSION)

    # Create one endpoint per tool so FastApiMCP can expose them as MCP tools
    for tool in TOOLS:
        schema = tool.inputSchema if isinstance(tool.inputSchema, dict) else {}

        def make_endpoint(t: Tool):

    server = create_server()
    app = FastAPI(title=SERVER_NAME, version=SERVER_VERSION)

    # Create one endpoint per tool so FastApiMCP can expose them as MCP tools
    for tool in server.tools:
        schema = tool.inputSchema if isinstance(tool.inputSchema, dict) else {}

        def make_endpoint(t: Tool):
            async def endpoint(data: Dict[str, Any] = Body(..., openapi_schema=schema)):

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

        return server.tools

    # Mount the MCP SSE interface
    FastApiMCP(app).mount()


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
