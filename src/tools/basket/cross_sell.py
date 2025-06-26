#!/usr/bin/env python3
# cross_sell_opportunities.py – 2025-06-25
# Ready for production: paste into your tools package and hot-reload.

from __future__ import annotations

from typing import Any, Dict, Optional
from mcp.types import Tool

from ...db.connection import execute_query
from ..utils import validate_date_range, create_tool_response

# ────────────────────────────────────────────────────────────────
# Implementation
# ────────────────────────────────────────────────────────────────
async def cross_sell_opportunities_impl(
    item_id: int,
    start_date: str,
    end_date: str,
    site_id: Optional[int] = 0,      # 0 → all sites
    top_n: int = 10,
) -> Dict[str, Any]:
    """
    Return the top-N items most frequently purchased in the same
    transactions as the target `item_id`.

    * `site_id = 0` or `None` → ignore site filter (all locations).
    * `site_id > 0`           → limit to that site only.
    """

    start_date, end_date = validate_date_range(start_date, end_date)

    # Build SQL — add site predicate only when a positive site_id is supplied
    site_pred = "AND SiteID = :site_id" if site_id and site_id > 0 else ""

    sql = f"""
    SELECT TOP (:top_n)
           s.ItemID,
           s.ItemName,
           COUNT(*)               AS pair_count,
           SUM(s.QtySold)         AS total_qty,
           SUM(s.GrossSales)      AS total_sales
    FROM   dbo.V_LLM_SalesFact s
    JOIN  (  SELECT DISTINCT TransactionID
             FROM   dbo.V_LLM_SalesFact
             WHERE  ItemID  = :item_id
               AND  SaleDate BETWEEN :start_date AND :end_date
               {site_pred}
           ) t
          ON s.TransactionID = t.TransactionID
    WHERE  s.ItemID <> :item_id
           {site_pred}
    GROUP  BY s.ItemID, s.ItemName
    ORDER  BY pair_count DESC;
    """

    params: Dict[str, Any] = {
        "top_n":      top_n,
        "item_id":    item_id,
        "start_date": start_date,
        "end_date":   end_date,
    }
    if site_id and site_id > 0:
        params["site_id"] = site_id

    try:
        rows = execute_query(sql, params)

        # Cast numerics for JSON serialisation
        for r in rows:
            r["total_qty"]   = float(r["total_qty"])
            r["total_sales"] = float(r["total_sales"])

        meta = {
            "target_item_id": item_id,
            "date_range": f"{start_date} → {end_date}",
            "site_id": site_id,
            "top_n": top_n,
        }
        return create_tool_response(rows, sql, params, meta)

    except Exception as exc:   # noqa: BLE001
        return create_tool_response([], sql, params, error=str(exc))

# ────────────────────────────────────────────────────────────────
# Tool registration
# ────────────────────────────────────────────────────────────────
cross_sell_opportunities_tool = Tool(
    name="cross_sell_opportunities",
    description=(
        "Identify the products most often purchased in the same transactions as"
        " the target item. Helps surface cross-selling and merchandising oppor-"
        "tunities and can be limited to a single site."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "item_id":    {"type": "integer", "description": "Target item ID"},
            "start_date": {"type": "string",  "format": "date"},
            "end_date":   {"type": "string",  "format": "date"},
            "site_id":    {
                "type": "integer",
                "minimum": 0,
                "default": 0,
                "description": "0 = all sites; positive value limits to one site",
            },
            "top_n": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 10,
                "description": "Maximum number of cross-sell items to return",
            },
        },
        "required": ["item_id", "start_date", "end_date"],
        "additionalProperties": False,
    },
)
cross_sell_opportunities_tool._implementation = cross_sell_opportunities_impl
