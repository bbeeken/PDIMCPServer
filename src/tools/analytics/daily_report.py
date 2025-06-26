<<<<<<< jy809i-codex/extend-daily_report_impl-with-optional-filters
"""Summarize daily sales totals with optional filters."""
=======
<<<<<<< codex/extend-daily_report_impl-with-optional-filters
"""Summarize daily sales totals with optional filters."""
=======
"""Daily sales totals grouped by date."""
>>>>>>> main
>>>>>>> main

from typing import Optional, Dict, Any

from mcp.types import Tool
<<<<<<< jy809i-codex/extend-daily_report_impl-with-optional-filters

=======
<<<<<<< codex/extend-daily_report_impl-with-optional-filters

=======
>>>>>>> main
>>>>>>> main
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response


async def daily_report_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
<<<<<<< jy809i-codex/extend-daily_report_impl-with-optional-filters
=======
<<<<<<< codex/extend-daily_report_impl-with-optional-filters
>>>>>>> main
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
<<<<<<< jy809i-codex/extend-daily_report_impl-with-optional-filters
=======
=======
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
>>>>>>> main
>>>>>>> main
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - db errors depend on env
        return create_tool_response([], sql, params, error=str(e))


daily_report_tool = Tool(
    name="daily_report",
    description=(
<<<<<<< jy809i-codex/extend-daily_report_impl-with-optional-filters
        "Summarise sales by day. Optional filters allow narrowing by site, "
        "item or category."
=======
<<<<<<< codex/extend-daily_report_impl-with-optional-filters
        "Summarise sales by day. Optional filters allow narrowing by site, "
        "item or category."
=======
        "Summarise transaction counts, quantities and sales totals for each day "
        "within the selected date range."
>>>>>>> main
>>>>>>> main
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "site_id": {"type": "integer", "description": "Optional site filter"},
<<<<<<< jy809i-codex/extend-daily_report_impl-with-optional-filters
=======
<<<<<<< codex/extend-daily_report_impl-with-optional-filters
>>>>>>> main
            "item_id": {"type": "integer", "description": "Exact item ID"},
            "item_name": {"type": "string", "description": "Item name (partial match)"},
            "category": {
                "type": "string",
                "description": "Category filter (partial match)",
            },
<<<<<<< jy809i-codex/extend-daily_report_impl-with-optional-filters
=======
=======
>>>>>>> main
>>>>>>> main
        },
        "required": ["start_date", "end_date"],
        "additionalProperties": False,
    },
)
<<<<<<< jy809i-codex/extend-daily_report_impl-with-optional-filters

=======
<<<<<<< codex/extend-daily_report_impl-with-optional-filters

=======
>>>>>>> main
>>>>>>> main
daily_report_tool._implementation = daily_report_impl
