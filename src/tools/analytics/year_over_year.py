#!/usr/bin/env python3
"""
year_over_year.py – Compare any period’s sales with the same period
last year.  Ready for production, no placeholders.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from dateutil.relativedelta import relativedelta  # pip install python-dateutil
from mcp.types import Tool

from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import (
    validate_date_range,
    create_tool_response,
    safe_divide,
)


# ────────────────────────────────────────────────────────────────
# Helper
# ────────────────────────────────────────────────────────────────
def _coerce_site(site_id: Optional[int | str]) -> Optional[int]:
    """Return positive int or None (0 / empty → None)."""
    if site_id in (None, "", 0, "0"):
        return None
    try:
        return int(site_id) if int(site_id) > 0 else None
    except (TypeError, ValueError):
        return None


# ────────────────────────────────────────────────────────────────
# Implementation
# ────────────────────────────────────────────────────────────────
async def year_over_year_impl(
    start_date: str,
    end_date: str,
    site_id: Optional[int | str] = 0,
) -> Dict[str, Any]:
    """Return current vs. prior-year totals plus % change."""
    start_date, end_date = validate_date_range(start_date, end_date)

    site_id_int = _coerce_site(site_id)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt   = datetime.strptime(end_date,   "%Y-%m-%d").date()

    prev_start = (start_dt - relativedelta(years=1)).isoformat()
    prev_end   = (end_dt   - relativedelta(years=1)).isoformat()

    base_sql = f"""
    SELECT
        SUM(GrossSales)                     AS TotalSales,
        SUM(QtySold)                        AS TotalQuantity,
        COUNT(DISTINCT TransactionID)       AS TransactionCount
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN :start_date AND :end_date
    """

    def run_query(s: str, e: str) -> tuple[Dict[str, Any], str, Dict[str, Any]]:
        params: Dict[str, Any] = {"start_date": s, "end_date": e}
        query = base_sql
        if site_id_int:
            query += " AND SiteID = :site_id"
            params["site_id"] = site_id_int

        rows = execute_query(query, params)
        result = (
            rows[0]
            if rows
            else {"TotalSales": 0, "TotalQuantity": 0, "TransactionCount": 0}
        )
        return result, query, params

    current, sql_curr, params_curr = run_query(start_date, end_date)
    previous, sql_prev, params_prev = run_query(prev_start, prev_end)

    change = {
        "sales_change_pct": safe_divide(
            current["TotalSales"] - previous["TotalSales"],
            previous["TotalSales"],
            0.0,
        ),
        "quantity_change_pct": safe_divide(
            current["TotalQuantity"] - previous["TotalQuantity"],
            previous["TotalQuantity"],
            0.0,
        ),
        "transaction_change_pct": safe_divide(
            current["TransactionCount"] - previous["TransactionCount"],
            previous["TransactionCount"],
            0.0,
        ),
    }

    data = {
        "current_period":   current,
        "previous_period":  previous,
        "change":           change,
    }

    metadata = {
        "current_range":  f"{start_date} to {end_date}",
        "previous_range": f"{prev_start} to {prev_end}",
        "site_id":        site_id_int,
    }

    debug_sql = (
        f"Current [{start_date}→{end_date}]: {sql_curr} "
        f"| Previous [{prev_start}→{prev_end}]: {sql_prev}"
    )

    merged_params = {**params_curr, **{f"prev_{k}": v for k, v in params_prev.items()}}

    return create_tool_response(data, debug_sql, merged_params, metadata)


# ────────────────────────────────────────────────────────────────
# Tool declaration
# ────────────────────────────────────────────────────────────────
year_over_year_tool = Tool(
    name="year_over_year",
    description=(
        "Compare totals for the selected period with the same date range in the "
        "prior year and report the percent change."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "format": "date"},
            "end_date":   {"type": "string", "format": "date"},
            "site_id": {
                "type": "integer",
                "minimum": 0,
                "default": 0,
                "description": "0 = all sites; positive value limits to one site",
            },
        },
        "required": ["start_date", "end_date"],
        "additionalProperties": False,
    },
)
year_over_year_tool._implementation = year_over_year_impl
