"""Cross sell opportunities tool"""

from typing import Any, Dict, Optional

from mcp.types import Tool

from ...db.connection import execute_query
from ..utils import validate_date_range, create_tool_response


async def cross_sell_opportunities_impl(
    item_id: int,
    start_date: str,
    end_date: str,
    site_id: Optional[int] = None,
    top_n: int = 10,
) -> Dict[str, Any]:
    """Suggest complementary items frequently purchased with the target item."""

    start_date, end_date = validate_date_range(start_date, end_date)

    sql = """
    SELECT TOP (?)
        s.ItemID,
        s.ItemName,
        COUNT(*) AS pair_count,
        SUM(s.QtySold) AS total_qty,
        SUM(s.GrossSales) AS total_sales
    FROM dbo.V_LLM_SalesFact s
    JOIN (
        SELECT DISTINCT TransactionID
        FROM dbo.V_LLM_SalesFact
        WHERE ItemID = ?
          AND SaleDate BETWEEN ? AND ?
    """

    params = [top_n, item_id, start_date, end_date]

    if site_id is not None:
        sql += " AND SiteID = ?"
        params.append(site_id)

    sql += ") t ON s.TransactionID = t.TransactionID\n"
    sql += "WHERE s.ItemID != ?"
    params.append(item_id)

    if site_id is not None:
        sql += " AND s.SiteID = ?"
        params.append(site_id)

    sql += "\nGROUP BY s.ItemID, s.ItemName\nORDER BY pair_count DESC"

    try:
        results = execute_query(sql, params)

        for row in results:
            if "total_qty" in row and row["total_qty"] is not None:
                row["total_qty"] = float(row["total_qty"])
            if "total_sales" in row and row["total_sales"] is not None:
                row["total_sales"] = float(row["total_sales"])

        metadata = {
            "target_item_id": item_id,
            "date_range": f"{start_date} to {end_date}",
            "site_id": site_id,
            "top_n": top_n,
        }

        return create_tool_response(results, sql, params, metadata)

    except Exception as e:  # pragma: no cover - database errors are environment specific
        return create_tool_response([], sql, params, error=str(e))


cross_sell_opportunities_tool = Tool(
    name="cross_sell_opportunities",
    description="Recommend items often purchased with a specified item",
    inputSchema={
        "type": "object",
        "properties": {
            "item_id": {"type": "integer", "description": "Target item ID"},
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "site_id": {"type": "integer", "description": "Optional site filter"},
            "top_n": {"type": "integer", "description": "Maximum items to return", "default": 10},
        },
        "required": ["item_id", "start_date", "end_date"],
    },
)

cross_sell_opportunities_tool._implementation = cross_sell_opportunities_impl

# Alias retained for backwards compatibility in tests
cross_sell_tool = cross_sell_opportunities_tool

