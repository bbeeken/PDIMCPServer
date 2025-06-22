"""Year-over-year sales comparison tool."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dateutil.relativedelta import relativedelta
from mcp.types import Tool
from ...db.connection import execute_query
from ..utils import validate_date_range, create_tool_response, safe_divide

async def year_over_year_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None
) -> Dict[str, Any]:
    """Compare sales for the given period against the previous year."""
    start_date, end_date = validate_date_range(start_date, end_date)

    prev_start = (datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(years=1)).strftime("%Y-%m-%d")
    prev_end = (datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(years=1)).strftime("%Y-%m-%d")

    base_sql = """
    SELECT
        SUM(GrossSales) AS TotalSales,
        SUM(QtySold) AS TotalQuantity,
        COUNT(DISTINCT TransactionID) AS TransactionCount
    FROM dbo.V_LLM_SalesFact
    WHERE SaleDate BETWEEN ? AND ?
    """

    def run_query(start: str, end: str) -> Dict[str, Any]:
        sql = base_sql
        params = [start, end]
        if site_id is not None:
            sql += " AND SiteID = ?"
            params.append(site_id)
        rows = execute_query(sql, params)
        row = rows[0] if rows else {"TotalSales": 0, "TotalQuantity": 0, "TransactionCount": 0}
        return row, sql, params

    try:
        current, sql_c, params_c = run_query(start_date, end_date)
        previous, sql_p, params_p = run_query(prev_start, prev_end)

        change = {
            "sales_change_pct": safe_divide(current["TotalSales"] - previous["TotalSales"], previous["TotalSales"], 0.0),
            "quantity_change_pct": safe_divide(current["TotalQuantity"] - previous["TotalQuantity"], previous["TotalQuantity"], 0.0),
            "transaction_change_pct": safe_divide(current["TransactionCount"] - previous["TransactionCount"], previous["TransactionCount"], 0.0),
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
        return create_tool_response(data, sql_c + " | " + sql_p, params_c + params_p, metadata)
    except Exception as e:  # pragma: no cover - database errors are environment specific
        return create_tool_response({}, base_sql, [], error=str(e))

year_over_year_tool = Tool(
    name="year_over_year",
    description="Compare sales with the same period last year",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "site_id": {"type": "integer", "description": "Optional site filter"}
        },
        "required": ["start_date", "end_date"]
    },
)

year_over_year_tool._implementation = year_over_year_impl

