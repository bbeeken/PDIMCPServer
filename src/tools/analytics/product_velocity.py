"""Compute the rate at which products sell over time (stub).

`product_velocity` is planned to measure how quickly inventory moves through
the system.  The implementation will integrate with more detailed inventory
data in a future release.
"""

from typing import Any, Dict, Optional

from mcp.types import Tool


async def product_velocity_impl(
    item_id: int,
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Placeholder implementation returning a not implemented message."""

    return {
        "success": False,
        "error": "product_velocity tool not yet implemented",
        "parameters": {
            "item_id": item_id,
            "start_date": start_date,
            "end_date": end_date,
            "site_id": site_id,
        },
    }


product_velocity_tool = Tool(
    name="product_velocity",
    description="Calculate how quickly items sell (stub)",
    inputSchema={
        "type": "object",
        "properties": {
            "item_id": {"type": "integer", "description": "Target item"},
            "start_date": {"type": "string", "description": "Start date"},
            "end_date": {"type": "string", "description": "End date"},
            "site_id": {"type": "integer", "description": "Optional site filter"},
        },
        "required": ["item_id", "start_date", "end_date"],
    },
)
product_velocity_tool._implementation = product_velocity_impl
