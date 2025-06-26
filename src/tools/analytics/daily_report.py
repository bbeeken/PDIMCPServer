"""Daily sales totals grouped by date."""

from typing import Optional, Dict, Any

from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response


async def daily_report_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Aggregate quantity and sales totals by day for a date range."""
    start_date, end_date = validate_date_range(start_date, end_date)
    sql = f"""
    SELECT CAST(SaleDate AS date) AS SaleDate,
           SUM(GrossSales) AS total_sales,
           SUM(QtySold) AS total_quantity,
           COUNT(DISTINCT TransactionID) AS transaction_count
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN :start_date AND :end_date
    """
    params: Dict[str, Any] = {"start_date": start_date, "end_date": end_date}
    if site_id is not None:
        sql += " AND SiteID = :site_id"
        params["site_id"] = site_id
    sql += " GROUP BY CAST(SaleDate AS date) ORDER BY SaleDate"
    try:
        results = execute_query(sql, params)
        metadata = {"date_range": f"{start_date} to {end_date}", "site_id": site_id}
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - db errors depend on env
        return create_tool_response([], sql, params, error=str(e))


daily_report_tool = Tool(
    name="daily_report",
    description=(
        "Summarise transaction counts, quantities and sales totals for each day "
        "within the selected date range."
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
daily_report_tool._implementation = daily_report_impl
