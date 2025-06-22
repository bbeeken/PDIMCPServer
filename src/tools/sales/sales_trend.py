"""
Sales trend analysis tool
"""

from typing import Optional, Dict, Any
from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response


async def sales_trend_impl(
    start_date: str,
    end_date: str,
    interval: str = "daily",
    site_id: Optional[int] = None,
    category: Optional[str] = None,
    metric: str = "sales",
) -> Dict[str, Any]:
    """Analyze sales trends over time"""
    start_date, end_date = validate_date_range(start_date, end_date)

    # Map interval to SQL
    interval_mapping = {
        "daily": "SaleDate",
        "weekly": "DATEPART(WEEK, SaleDate) as Week, DATEPART(YEAR, SaleDate) as Year",
        "monthly": "DATEPART(MONTH, SaleDate) as Month, DATEPART(YEAR, SaleDate) as Year",
        "hourly": "SaleDate, DATEPART(HOUR, TimeOfDay) as Hour",
    }

    interval_key = interval.lower()
    if interval_key not in interval_mapping:
        error = f"Invalid interval: {interval}"
        return create_tool_response([], "", [], error=error)

    metric_mapping = {
        "sales": ("SUM(GrossSales)", "TotalSales"),
        "quantity": ("SUM(QtySold)", "TotalQuantity"),
        "transactions": ("COUNT(DISTINCT TransactionID)", "TransactionCount"),
    }

    metric_key = metric.lower()
    if metric_key not in metric_mapping:
        error = f"Invalid metric: {metric}"
        return create_tool_response([], "", [], error=error)

    metric_sql, metric_alias = metric_mapping[metric_key]

    interval_sql = interval_mapping[interval_key]

    sql = f"""
    SELECT
        {interval_sql},
        {metric_sql} AS {metric_alias}
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN ? AND ?
    """

    params = [start_date, end_date]

    if site_id:
        sql += " AND SiteID = ?"
        params.append(site_id)

    if category:
        sql += " AND Category LIKE ?"
        params.append(f"%{category}%")

    group_cols = ", ".join(part.split(" as ")[0] for part in interval_sql.split(", "))
    sql += f" GROUP BY {group_cols}"
    sql += f" ORDER BY {group_cols}"

    try:
        results = execute_query(sql, params)

        for row in results:
            if "SaleDate" in row and row["SaleDate"]:
                row["SaleDate"] = str(row["SaleDate"])
            if "TimeOfDay" in row and row["TimeOfDay"]:
                row["TimeOfDay"] = str(row["TimeOfDay"])

        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "interval": interval_key,
            "metric": metric_key,
            "filters": {"site_id": site_id, "category": category},
        }

        return create_tool_response(results, sql, params, metadata)

    except Exception as e:
        return create_tool_response([], sql, params, error=str(e))


# Tool definition
sales_trend_tool = Tool(
    name="sales_trend",
    description="Analyze sales trends over time",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Start date (YYYY-MM-DD)",
            },
            "end_date": {
                "type": "string",
                "description": "End date (YYYY-MM-DD)",
            },
            "interval": {
                "type": "string",
                "enum": ["daily", "weekly", "monthly", "hourly"],
                "default": "daily",
                "description": "Time interval for aggregation",
            },
            "site_id": {
                "type": "integer",
                "description": "Optional site filter",
            },
            "category": {
                "type": "string",
                "description": "Optional category filter",
            },
            "metric": {
                "type": "string",
                "enum": ["sales", "quantity", "transactions"],
                "default": "sales",
                "description": "Metric to aggregate",
            },
        },
        "required": ["start_date", "end_date"],
    },
)

sales_trend_tool._implementation = sales_trend_impl
