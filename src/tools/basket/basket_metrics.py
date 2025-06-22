"""Basic basket size metrics."""

from typing import Any, Dict, Optional

from mcp.types import Tool

from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response


async def basket_metrics_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Calculate overall basket metrics for a date range."""
    start_date, end_date = validate_date_range(start_date, end_date)

    sql = f"""
    SELECT
        COUNT(DISTINCT TransactionID) AS transaction_count,
        SUM(QtySold) AS total_quantity,
        SUM(GrossSales) AS total_sales,
        AVG(QtySold) AS avg_items_per_tx
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN ? AND ?
    """
    params = [start_date, end_date]
    if site_id is not None:
        sql += " AND SiteID = ?"
        params.append(site_id)

    try:
        results = execute_query(sql, params)
        metadata = {"date_range": f"{start_date} to {end_date}", "site_id": site_id}
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - depends on DB state
        return create_tool_response([], sql, params, error=str(e))


basket_metrics_tool = Tool(
    name="basket_metrics",
    description="Calculate basket metrics like average items per transaction",
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
basket_metrics_tool._implementation = basket_metrics_impl
