"""Aggregate basket-level statistics.

This module will eventually expose a tool that calculates metrics such as the
average basket value and item count.  The current implementation only provides
a minimal stub so that imports succeed.
"""

from typing import Any, Dict, List, Optional

from mcp.types import Tool


async def basket_metrics_impl(
    start_date: str,
    end_date: str,
    group_by: Optional[List[str]] = None,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Stub implementation for future basket metrics calculations."""

    # TODO: integrate with ``BasketRepository.basket_metrics`` to perform the
    # actual aggregation once the database schema is finalized.
    return {
        "success": False,
        "error": "basket_metrics tool not yet implemented",
        "parameters": {
            "start_date": start_date,
            "end_date": end_date,
            "group_by": group_by,
            "site_id": site_id,
        },
    }


basket_metrics_tool = Tool(
    name="basket_metrics",
    description="Calculate basket-level statistics (stub)",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date"},
            "end_date": {"type": "string", "description": "End date"},
            "group_by": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional grouping columns",
            },
            "site_id": {"type": "integer", "description": "Filter by site"},
        },
        "required": ["start_date", "end_date"],
    },
)
basket_metrics_tool._implementation = basket_metrics_impl
