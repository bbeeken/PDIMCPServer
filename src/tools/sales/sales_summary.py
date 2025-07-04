#!/usr/bin/env python3
# sales_summary.py – v2025-06-25 • fixed TextClause→str

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy.sql import text

from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response

_ALLOWED_GROUPS: Dict[str, str] = {
    "date": "CAST(SaleDate AS date)",
    "hour": "DATEPART(HOUR, TimeOfDay)",
    "site": "SiteID, SiteName",
    "category": "Category",
    "department": "Department",
    "dayofweek": "DayOfWeek",
}


@dataclass(slots=True)
class Params:
    start_date: date
    end_date: date
    group_by: List[str]
    site_id: Optional[int]
    category: Optional[str]
    item_id: Optional[int]
    item_name: Optional[str]


async def sales_summary_impl(
    start_date: str,
    end_date: str,
    group_by: Optional[List[str]] = None,
    site_id: Optional[int] = None,
    category: Optional[str] = None,
    item_id: Optional[int] = None,
    item_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Aggregate sales KPIs with flexible grouping."""
    start_date, end_date = validate_date_range(start_date, end_date)
    p = Params(
        start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
        end_date=datetime.strptime(end_date, "%Y-%m-%d").date(),
        group_by=group_by or [],
        site_id=site_id if site_id and site_id > 0 else None,
        category=category.strip() if category else None,
        item_id=item_id if item_id and item_id > 0 else None,
        item_name=item_name.strip() if item_name else None,
    )

    illegal = set(p.group_by) - _ALLOWED_GROUPS.keys()
    if illegal:
        raise ValueError(f"Unsupported group_by value(s): {', '.join(illegal)}")

    sel, grp = [], []
    for g in p.group_by:
        cols = _ALLOWED_GROUPS[g].split(", ")
        sel.extend(cols)
        grp.extend(cols)

    select_sql = ",\n            ".join(sel) + (",\n            " if sel else "")
    group_sql = f"GROUP BY {', '.join(grp)}" if grp else ""
    order_sql = f"ORDER BY {', '.join(sel)}" if sel else ""

    stmt = text(
        f"""
        SELECT
            {select_sql}
            COUNT(DISTINCT TransactionID)                      AS TransactionCount,
            COUNT(DISTINCT ItemID)                       AS UniqueItems,
            SUM(QtySold)                                       AS TotalQuantity,
            SUM(GrossSales)                                    AS TotalSales,
            CASE WHEN COUNT(DISTINCT TransactionID)=0
                 THEN 0
                 ELSE SUM(GrossSales) /
                      CAST(COUNT(DISTINCT TransactionID) AS decimal(18,4))
            END                                                AS AvgSaleAmount
        FROM   {SALES_FACT_VIEW}
        WHERE  SaleDate BETWEEN :start_date AND :end_date
        {"AND  SiteID = :site_id"        if p.site_id   else ""}
        {"AND  Category LIKE :category"  if p.category else ""}
        {"AND  ItemID = :item_id"        if p.item_id   else ("AND  ItemName LIKE :item_name" if p.item_name else "")}
        {group_sql}
        {order_sql}
    """
    )

    bind = {
        "start_date": p.start_date,
        "end_date": p.end_date,
        **({"site_id": p.site_id} if p.site_id else {}),
        **({"category": f"%{p.category}%"} if p.category else {}),
        **({"item_id": p.item_id} if p.item_id else {}),
        **({"item_name": f"%{p.item_name}%"} if p.item_name and not p.item_id else {}),
    }

    try:
        # FIX: convert TextClause → str for execute_query
        rows = execute_query(str(stmt), bind)

        for r in rows:
            if "SaleDate" in r:
                r["SaleDate"] = str(r["SaleDate"])

        meta = {
            "date_range": f"{p.start_date} → {p.end_date}",
            "grouping": p.group_by or "overall",
            "filters": {
                "site_id": p.site_id,
                "category": p.category,
                "item_id": p.item_id,
                "item_name": p.item_name,
            },
        }
        return create_tool_response(rows, str(stmt), bind, meta)
    except Exception as exc:  # noqa: BLE001
        return create_tool_response([], str(stmt), bind, error=str(exc))


sales_summary_tool = Tool(
    name="sales_summary",
    description=(
        "Aggregate sales metrics such as transactions, quantity and total sales. "
        "Use the `group_by` option to summarize by date, hour, site, category or "
        "department. Supports optional item ID or name filters."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "format": "date"},
            "end_date": {"type": "string", "format": "date"},
            "group_by": {
                "type": "array",
                "items": {"type": "string", "enum": list(_ALLOWED_GROUPS.keys())},
            },
            "site_id": {"type": "integer", "minimum": 0},
            "category": {"type": "string"},
            "item_id": {"type": "integer", "minimum": 0},
            "item_name": {"type": "string"},
        },
        "required": ["start_date", "end_date"],
        "additionalProperties": False,
    },
)
sales_summary_tool._implementation = sales_summary_impl
