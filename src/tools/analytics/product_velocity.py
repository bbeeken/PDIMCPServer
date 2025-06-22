
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

"""Identify top selling items in a period."""
from typing import Optional, Dict, Any, List
from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response

async def product_velocity_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """Return the top selling items sorted by quantity."""
    start_date, end_date = validate_date_range(start_date, end_date)
    sql = f"""
    SELECT TOP (?) ItemID, ItemName,
           SUM(QtySold) AS total_quantity,
           SUM(GrossSales) AS total_sales
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN ? AND ?
    """
    params: List[Any] = [limit, start_date, end_date]
    if site_id is not None:
        sql += " AND SiteID = ?"
        params.append(site_id)
    sql += " GROUP BY ItemID, ItemName ORDER BY total_quantity DESC"
    try:
        results = execute_query(sql, params)
        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "site_id": site_id,
            "limit": limit,
        }
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:
        return create_tool_response([], sql, params, error=str(e))

product_velocity_tool = Tool(
    name="product_velocity",
    description="List top selling items for a period",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "site_id": {"type": "integer", "description": "Optional site filter"},
            "limit": {"type": "integer", "default": 10, "description": "Maximum items to return"},
        },
        "required": ["start_date", "end_date"],

    },
)
product_velocity_tool._implementation = product_velocity_impl
