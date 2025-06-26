"""Aggregate sales by hour."""

from typing import Optional, Dict, Any
from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response


async def hourly_sales_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Aggregate quantity and sales totals by hour for a date range."""
    start_date, end_date = validate_date_range(start_date, end_date)
    sql = f"""
    SELECT
        DATEPART(HOUR, TimeOfDay) AS hour,
        SUM(QtySold) AS total_quantity,
        SUM(GrossSales) AS total_sales,
        COUNT(DISTINCT TransactionID) AS transaction_count
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN :start_date AND :end_date
    """
    params = {"start_date": start_date, "end_date": end_date}
    if site_id is not None:
        sql += " AND SiteID = :site_id"
        params["site_id"] = site_id
    sql += " GROUP BY DATEPART(HOUR, TimeOfDay) ORDER BY hour"
    try:
        results = execute_query(sql, params)
        metadata = {"date_range": f"{start_date} to {end_date}", "site_id": site_id}
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - db errors depend on env
        return create_tool_response([], sql, params, error=str(e))


hourly_sales_tool = Tool(
    name="hourly_sales",
    description=(
        "Summarise transaction counts, quantities and sales totals for each hour"
        " of the day within the selected date range."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "site_id": {"type": "integer", "description": "Optional site filter"},
        },
        "required": ["start_date", "end_date"],
        "additionalProperties": False,
    },
)
hourly_sales_tool._implementation = hourly_sales_impl
