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
    SELECT TOP (:limit) ItemID, ItemName,
           SUM(QtySold) AS total_quantity,
           SUM(GrossSales) AS total_sales
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN :start_date AND :end_date
    """
    params: Dict[str, Any] = {
        "limit": limit,
        "start_date": start_date,
        "end_date": end_date,
    }
    if site_id is not None:
        sql += " AND SiteID = :site_id"
        params["site_id"] = site_id
    sql += " GROUP BY ItemID, ItemName ORDER BY total_quantity DESC"
    try:
        results = execute_query(sql, params)
        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "site_id": site_id,
            "limit": limit,
        }
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - db errors depend on env
        return create_tool_response([], sql, params, error=str(e))


product_velocity_tool = Tool(
    name="product_velocity",
    description=(
        "List the fastest selling items within the date range ranked by total "
        "quantity. Optionally filter to a specific site and control the number "
        "of results."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "site_id": {"type": "integer", "description": "Optional site filter"},
            "limit": {
                "type": "integer",
                "default": 10,
                "description": "Maximum items to return",
            },
        },
        "required": ["start_date", "end_date"],
        "additionalProperties": False,
    },
)
product_velocity_tool._implementation = product_velocity_impl
