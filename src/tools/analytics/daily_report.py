"""Summarize daily sales totals with optional filters."""

from typing import Optional, Dict, Any

from mcp.types import Tool

from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response


async def daily_report_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
    item_id: Optional[int] = None,
    item_name: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Return daily totals for quantity, sales and transactions."""

    start_date, end_date = validate_date_range(start_date, end_date)

    sql = f"""
    SELECT
        SaleDate,
        SUM(QtySold) AS total_quantity,
        SUM(GrossSales) AS total_sales,
        COUNT(DISTINCT TransactionID) AS transaction_count
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN :start_date AND :end_date
    """

    params: Dict[str, Any] = {"start_date": start_date, "end_date": end_date}

    if site_id is not None:
        sql += " AND SiteID = :site_id"
        params["site_id"] = site_id

    if item_id is not None:
        sql += " AND ItemID = :item_id"
        params["item_id"] = item_id
    elif item_name:
        sql += " AND ItemName LIKE :item_name"
        params["item_name"] = f"%{item_name}%"

    if category:
        sql += " AND Category LIKE :category"
        params["category"] = f"%{category}%"

    sql += " GROUP BY SaleDate ORDER BY SaleDate"

    try:
        results = execute_query(sql, params)
        for row in results:
            if "SaleDate" in row and row["SaleDate"]:
                row["SaleDate"] = str(row["SaleDate"])

        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "filters": {
                "site_id": site_id,
                "item_id": item_id,
                "item_name": item_name,
                "category": category,
            },
        }
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - db errors depend on env
        return create_tool_response([], sql, params, error=str(e))


daily_report_tool = Tool(
    name="daily_report",
    description=(
        "Summarise sales by day. Optional filters allow narrowing by site, "
        "item or category."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "site_id": {"type": "integer", "description": "Optional site filter"},
            "item_id": {"type": "integer", "description": "Exact item ID"},
            "item_name": {"type": "string", "description": "Item name (partial match)"},
            "category": {
                "type": "string",
                "description": "Category filter (partial match)",
            },
        },
        "required": ["start_date", "end_date"],
        "additionalProperties": False,
    },
)

daily_report_tool._implementation = daily_report_impl
