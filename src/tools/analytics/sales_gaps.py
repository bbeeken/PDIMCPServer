#!/usr/bin/env python3
# sales_gaps.py – 2025-06-25  (patched)

from __future__ import annotations
from datetime import date, timedelta, datetime
from typing import Dict, Any, List, Optional

from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response

# ───────────────────────────────────────────────────────────────
# Implementation
# ───────────────────────────────────────────────────────────────
async def sales_gaps_impl(
    start_date: str,
    end_date:   str,
    site_id:    Optional[int] = 0,   # 0 ⇒ all sites
) -> Dict[str, Any]:
    """
    Return a list of calendar dates in the range [start_date, end_date]
    for which **no** sales rows exist in V_LLM_SalesFact.
    """

    start_date, end_date = validate_date_range(start_date, end_date)

    # Half-open range protects against time components
    site_pred = "AND SiteID = :site_id" if site_id and site_id > 0 else ""
    sql = f"""
        SELECT DISTINCT CONVERT(date, SaleDate) AS SaleDay
        FROM {SALES_FACT_VIEW}
        WHERE SaleDate >= :start_date
          AND SaleDate <  DATEADD(day, 1, :end_date)
          {site_pred}
    """

    params: Dict[str, Any] = {
        "start_date": start_date,
        "end_date":   end_date,
    }
    if site_id and site_id > 0:
        params["site_id"] = site_id

    try:
        rows = execute_query(sql, params)
        sold_days = {row["SaleDay"] for row in rows}

        # Generate full date range and find gaps
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt   = datetime.strptime(end_date,   "%Y-%m-%d").date()

        gap_days: List[str] = []
        cur = start_dt
        while cur <= end_dt:
            if cur not in sold_days:
                gap_days.append(cur.isoformat())
            cur += timedelta(days=1)

        meta = {
            "date_range": f"{start_date} → {end_date}",
            "site_id": site_id,
        }
        return create_tool_response(gap_days, sql, params, meta)

    except Exception as exc:  # noqa: BLE001
        return create_tool_response([], sql, params, error=str(exc))

# ───────────────────────────────────────────────────────────────
# Tool registration
# ───────────────────────────────────────────────────────────────
sales_gaps_tool = Tool(
    name="sales_gaps",
    description=(
        "List calendar days within the range that have no sales records in "
        "V_LLM_SalesFact. Useful for spotting data outages or store closures."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "format": "date"},
            "end_date":   {"type": "string", "format": "date"},
            "site_id":    {
                "type": "integer",
                "minimum": 0,
                "default": 0,
                "description": "0 = all sites; positive to filter one site",
            },
        },
        "required": ["start_date", "end_date"],
        "additionalProperties": False,
    },
)
sales_gaps_tool._implementation = sales_gaps_impl
