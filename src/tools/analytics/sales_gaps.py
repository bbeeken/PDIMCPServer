"""Identify dates within a range that have no recorded sales."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response


async def sales_gaps_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Return a list of dates where no sales exist."""
    start_date, end_date = validate_date_range(start_date, end_date)
    sql = f"SELECT DISTINCT SaleDate FROM {SALES_FACT_VIEW} WHERE SaleDate BETWEEN ? AND ?"
    params: List[Any] = [start_date, end_date]
    if site_id is not None:
        sql += " AND SiteID = ?"
        params.append(site_id)
    try:
        rows = execute_query(sql, params)
        sold_dates = {row["SaleDate"] for row in rows}
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        gap_dates = []
        curr = start_dt
        while curr <= end_dt:
            if curr not in sold_dates:
                gap_dates.append(curr.isoformat())
            curr += timedelta(days=1)
        metadata = {"date_range": f"{start_date} to {end_date}", "site_id": site_id}
        return create_tool_response(gap_dates, sql, params, metadata)
    except Exception as e:
        return create_tool_response([], sql, params, error=str(e))


sales_gaps_tool = Tool(
    name="sales_gaps",
    description="List dates in a range with no sales data",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "site_id": {"type": "integer", "description": "Optional site filter"},
        },
        "required": ["start_date", "end_date"],
    },
)
sales_gaps_tool._implementation = sales_gaps_impl
