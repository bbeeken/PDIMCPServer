"""Compare a period's sales with the same period last year."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response, safe_divide


async def year_over_year_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Return current and prior year sales totals and percent change."""
    start_date, end_date = validate_date_range(start_date, end_date)
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    prev_start = (start_dt - timedelta(days=365)).isoformat()
    prev_end = (end_dt - timedelta(days=365)).isoformat()
    base_sql = f"""
    SELECT
        SUM(GrossSales) AS TotalSales,
        SUM(QtySold) AS TotalQuantity,
        COUNT(DISTINCT TransactionID) AS TransactionCount
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN :start_date AND :end_date
    """

    def run_query(s: str, e: str):
        params = {"start_date": s, "end_date": e}
        query = base_sql
        if site_id:
            query += " AND SiteID = :site_id"
            params["site_id"] = site_id
        rows = execute_query(query, params)
        return (
            (
                rows[0]
                if rows
                else {"TotalSales": 0, "TotalQuantity": 0, "TransactionCount": 0}
            ),
            query,
            params,
        )

    current, sql_curr, params_curr = run_query(start_date, end_date)
    previous, sql_prev, params_prev = run_query(prev_start, prev_end)
    change = {
        "sales_change_pct": safe_divide(
            current["TotalSales"] - previous["TotalSales"], previous["TotalSales"], 0.0
        ),
        "quantity_change_pct": safe_divide(
            current["TotalQuantity"] - previous["TotalQuantity"],
            previous["TotalQuantity"],
            0.0,
        ),
        "transaction_change_pct": safe_divide(
            current["TransactionCount"] - previous["TransactionCount"],
            previous["TransactionCount"],
            0.0,
        ),
    }
    data = {
        "current_period": current,
        "previous_period": previous,
        "change": change,
    }
    metadata = {
        "current_range": f"{start_date} to {end_date}",
        "previous_range": f"{prev_start} to {prev_end}",
        "site_id": site_id,
    }
    debug_sql = f"Current: {sql_curr} | Previous: {sql_prev}"
    merged_params = {**params_curr, **{f"prev_{k}": v for k, v in params_prev.items()}}
    return create_tool_response(data, debug_sql, merged_params, metadata)


year_over_year_tool = Tool(
    name="year_over_year",
    description="Compare a period's sales with the prior year",
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
year_over_year_tool._implementation = year_over_year_impl
