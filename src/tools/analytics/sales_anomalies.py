"""Detect unusual spikes or drops in sales data (stub).

The full anomaly detection logic will be added later.  This placeholder keeps
the module importable and documents the intended behaviour.
"""

from typing import Any, Dict, Optional

from mcp.types import Tool


async def sales_anomalies_impl(
    start_date: str,
    end_date: str,
    threshold: float = 0.2,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Return a message noting that the feature is not implemented."""

    return {
        "success": False,
        "error": "sales_anomalies tool not yet implemented",
        "parameters": {
            "start_date": start_date,
            "end_date": end_date,
            "threshold": threshold,
            "site_id": site_id,
        },
    }


sales_anomalies_tool = Tool(
    name="sales_anomalies",
    description="Highlight unusual changes in sales (stub)",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date"},
            "end_date": {"type": "string", "description": "End date"},
            "threshold": {
                "type": "number",
                "description": "Percentage change considered anomalous",
                "default": 0.2,
            },
            "site_id": {"type": "integer", "description": "Optional site filter"},
        },
        "required": ["start_date", "end_date"],
    },
)
sales_anomalies_tool._implementation = sales_anomalies_impl
