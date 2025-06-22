
"""Hourly sales aggregation tool"""
from typing import Optional, Dict, Any
from mcp.types import Tool
from ...db.connection import execute_query

"""Hourly sales analysis"""
from typing import Optional, Dict, Any
from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW

from ..utils import validate_date_range, create_tool_response

async def hourly_sales_impl(
    start_date: str,
    end_date: str,

    site_id: Optional[int] = None

    site_id: Optional[int] = None,

) -> Dict[str, Any]:
    """Aggregate sales by hour within a date range."""
    start_date, end_date = validate_date_range(start_date, end_date)


    sql = """
    SELECT
        DATEPART(HOUR, TimeOfDay) AS Hour,
        SUM(GrossSales) AS TotalSales,
        SUM(QtySold) AS TotalQuantity,
        COUNT(DISTINCT TransactionID) AS TransactionCount
    FROM dbo.V_LLM_SalesFact
    WHERE SaleDate BETWEEN ? AND ?
    """
    params = [start_date, end_date]
    if site_id is not None:

    sql = f"""
    SELECT
        DATEPART(HOUR, TimeOfDay) AS Hour,
        SUM(QtySold) AS TotalQuantity,
        SUM(GrossSales) AS TotalSales,
        COUNT(DISTINCT TransactionID) AS TransactionCount
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN ? AND ?
    """
    params = [start_date, end_date]
    if site_id:

        sql += " AND SiteID = ?"
        params.append(site_id)
    sql += " GROUP BY DATEPART(HOUR, TimeOfDay) ORDER BY Hour"

    try:
        results = execute_query(sql, params)

        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "site_id": site_id,
        }
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - database errors are environment specific

        metadata = {"date_range": f"{start_date} to {end_date}", "site_id": site_id}
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:

        return create_tool_response([], sql, params, error=str(e))

hourly_sales_tool = Tool(
    name="hourly_sales",

    description="Aggregate sales totals by hour",

    description="Aggregate sales by hour for a given date range",

    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},

            "site_id": {"type": "integer", "description": "Optional site filter"}
        },
        "required": ["start_date", "end_date"]

            "site_id": {"type": "integer", "description": "Optional site filter"},
        },
        "required": ["start_date", "end_date"],

    },
)

hourly_sales_tool._implementation = hourly_sales_impl

