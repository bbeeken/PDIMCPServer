"""Determine hours with the highest sales."""
from typing import Optional, Dict, Any, List
from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response

async def peak_hours_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
    top_n: int = 5,
) -> Dict[str, Any]:
    """Return the top ``top_n`` hours by total sales."""
    start_date, end_date = validate_date_range(start_date, end_date)
    sql = f"""
    SELECT DATEPART(HOUR, TimeOfDay) AS hour,
           SUM(GrossSales) AS total_sales,
           SUM(QtySold) AS total_quantity,
           COUNT(DISTINCT TransactionID) AS transaction_count
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN ? AND ?
    """
    params: List[Any] = [start_date, end_date]
    if site_id is not None:
        sql += " AND SiteID = ?"
        params.append(site_id)
    sql += " GROUP BY DATEPART(HOUR, TimeOfDay)"
    try:
        results = execute_query(sql, params)
        results.sort(key=lambda r: r.get("total_sales", 0), reverse=True)
        results = results[:top_n]
        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "site_id": site_id,
            "top_n": top_n,
        }
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:
        return create_tool_response([], sql, params, error=str(e))

peak_hours_tool = Tool(
    name="peak_hours",
    description="Find the hours of day with the highest sales volume",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "site_id": {"type": "integer", "description": "Optional site filter"},
            "top_n": {"type": "integer", "default": 5, "description": "Number of hours to return"},
        },
        "required": ["start_date", "end_date"],
    },
)
peak_hours_tool._implementation = peak_hours_impl
