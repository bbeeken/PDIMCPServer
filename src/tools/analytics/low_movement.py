"""Identify slow-moving items based on quantity sold."""

from typing import Optional, Dict, Any, List

from mcp.types import Tool

from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response


async def low_movement_impl(
    start_date: str,
    end_date: str,
    threshold: int = 10,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Return items with quantity sold below ``threshold``."""
    start_date, end_date = validate_date_range(start_date, end_date)
    sql = f"""
    SELECT ItemID, ItemName, SUM(QtySold) AS total_quantity, SUM(GrossSales) AS total_sales
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN ? AND ?
    """
    params: List[Any] = [start_date, end_date]
    if site_id is not None:
        sql += " AND SiteID = ?"
        params.append(site_id)
    sql += " GROUP BY ItemID, ItemName HAVING SUM(QtySold) <= ? ORDER BY total_quantity"
    params.append(threshold)
    try:
        results = execute_query(sql, params)
        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "threshold": threshold,
            "site_id": site_id,
        }
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - db errors depend on env
        return create_tool_response([], sql, params, error=str(e))


low_movement_tool = Tool(
    name="low_movement",
    description="List items with low sales volume",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "threshold": {
                "type": "integer",
                "default": 10,
                "description": "Maximum quantity sold",
            },
            "site_id": {"type": "integer", "description": "Optional site filter"},
        },
        "required": ["start_date", "end_date"],
        "additionalProperties": False,
    },
)
low_movement_tool._implementation = low_movement_impl
