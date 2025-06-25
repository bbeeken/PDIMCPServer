"""Detect unusual spikes or drops in daily sales."""

from typing import Optional, Dict, Any, List
import statistics

from mcp.types import Tool

from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response


async def sales_anomalies_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
    z_score: float = 2.0,
) -> Dict[str, Any]:
    """Return dates where total sales deviate from the mean by ``z_score`` standard deviations."""
    start_date, end_date = validate_date_range(start_date, end_date)
    sql = f"""
    SELECT SaleDate, SUM(GrossSales) AS total_sales
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN ? AND ?
    """
    params: List[Any] = [start_date, end_date]
    if site_id is not None:
        sql += " AND SiteID = ?"
        params.append(site_id)
    sql += " GROUP BY SaleDate ORDER BY SaleDate"
    try:
        rows = execute_query(sql, params)
        totals = [r["total_sales"] for r in rows]
        mean = statistics.mean(totals) if totals else 0
        stdev = statistics.pstdev(totals) if len(totals) > 1 else 0
        anomalies = [
            r for r in rows if stdev and abs(r["total_sales"] - mean) > z_score * stdev
        ]
        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "site_id": site_id,
            "mean": mean,
            "stdev": stdev,
            "z_score": z_score,
        }
        return create_tool_response(anomalies, sql, params, metadata)
    except Exception as e:  # pragma: no cover - db errors depend on env
        return create_tool_response([], sql, params, error=str(e))


sales_anomalies_tool = Tool(
    name="sales_anomalies",
    description="Highlight days with abnormal sales totals",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "site_id": {"type": "integer", "description": "Optional site filter"},
            "z_score": {
                "type": "number",
                "default": 2.0,
                "description": "Standard deviation threshold",
            },
        },
        "required": ["start_date", "end_date"],
        "additionalProperties": False,
    },
)
sales_anomalies_tool._implementation = sales_anomalies_impl
