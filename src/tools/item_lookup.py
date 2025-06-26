"""Enhanced product lookup with RapidFuzz scoring.

This tool queries **PDI_Warehouse_1539_01.dbo.product_view** and supports:
• Exact *item_id* match
• Word‑order‑insensitive text search enhanced with **RapidFuzz** token‑set similarity for ranking
• Excludes brands marked **UNAUTH** / **DEAUTH**

It returns the *limit* highest‑scoring rows.
"""

from __future__ import annotations

import re
from typing import Optional, Dict, Any, List

from mcp.types import Tool
from ..db.connection import execute_query
from .utils import create_tool_response

try:
    from rapidfuzz import fuzz, process  # type: ignore
except ImportError:  # pragma: no cover – RapidFuzz optional but strongly recommended
    fuzz = None  # type: ignore
    process = None  # type: ignore

# ────────────────────────────────────────────────────────────────
# Implementation
# ────────────────────────────────────────────────────────────────

async def item_lookup_impl(  # noqa: N802 – fixed by framework
    item_id: Optional[int] = None,
    description: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Search **product_view** by *item_id* or *description* using RapidFuzz.

    Parameters
    ----------
    item_id : int | None
        Exact `Item_ID` to match.
    description : str | None
        Free‑text search; the words can be in any order and minor typos are OK.
    limit : int
        Number of rows returned after RapidFuzz ranking.
    """

    # ── Base SQL --------------------------------------------------------
    sql = (
        """
        SELECT TOP (?)
               Item_ID         AS item_id,
               Item_Desc       AS description,
               Category_Desc   AS category,
               Department_Desc AS department,
               UPC,
               Size_Desc       AS size,
               Brand
        FROM   PDI_Warehouse_1539_01.dbo.product_view WITH (NOLOCK)
        WHERE  UPPER(Brand) NOT LIKE '%UNAUTH%'
          AND  UPPER(Brand) NOT LIKE '%DEAUTH%'
        """
    )

    params: List[Any] = []

    # ------------------------------------------------------------------
    # Exact item lookup short‑circuits RapidFuzz
    # ------------------------------------------------------------------
    if item_id is not None:
        sql += " AND Item_ID = ? ORDER BY Item_Desc"
        params.extend([1, item_id])  # TOP 1 because ID is unique
        try:
            rows = execute_query(sql, params)
            return create_tool_response(rows, sql, params, {"filters": {"item_id": item_id}})
        except Exception as exc:  # pragma: no cover – DB‑specific
            return create_tool_response([], sql, params, error=str(exc))

    # ------------------------------------------------------------------
    # Description search – 2‑phase: SQL pre‑filter → RapidFuzz rank
    # ------------------------------------------------------------------
    if not description:
        return create_tool_response([], sql, params, error="Either item_id or description is required")

    # 1️⃣ Pre‑filter in SQL using LIKE on each token to shrink the candidate set
    tokens = [t.upper() for t in re.split(r"[\s,.;:-]+", description) if t]
    for token in tokens:
        sql += " AND UPPER(Item_Desc) LIKE ?"
        params.append(f"%{token}%")

    preliminary_limit = max(limit * 25, 250)  # fetch more than needed for ranking
    params.insert(0, preliminary_limit)  # first parameter is TOP ?

    sql += " ORDER BY Item_Desc"

    try:
        candidates = execute_query(sql, params)
    except Exception as exc:  # pragma: no cover
        return create_tool_response([], sql, params, error=str(exc))

    # 2️⃣ Rank with RapidFuzz (token_set_ratio)
    if fuzz and process:
        choices = [row["description"] for row in candidates]
        matches = process.extract(  # returns list[(str, score, idx)]
            description,
            choices,
            scorer=fuzz.token_set_ratio,
            limit=limit,
        )
        ranked_rows = [candidates[idx] | {"score": score} for _, score, idx in matches]
    else:  # fallback – return first *limit* results unsorted
        ranked_rows = candidates[:limit]

    metadata = {
        "filters": {
            "description": description,
            "tokens": tokens,
            "rapidfuzz": bool(fuzz),
            "limit": limit,
        }
    }
    return create_tool_response(ranked_rows, sql, params, metadata)


# ────────────────────────────────────────────────────────────────
# Tool registration
# ────────────────────────────────────────────────────────────────

item_lookup_tool = Tool(
    name="item_lookup",
    description=(
        "Look up authorised items in **product_view**. Accepts `item_id` for "
        "exact match or free‑text `description` with RapidFuzz fuzzy ranking. "
        "Example: ‘20oz coke’ → matches ‘COKE CLASSIC 20 OZ’."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "item_id": {
                "type": "integer",
                "description": "Exact item ID to match",
            },
            "description": {
                "type": "string",
                "description": "Free‑text search (word order & typos allowed)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum rows to return after ranking",
                "default": 50,
            },
        },
        "required": [],
        "additionalProperties": False,
    },
)

item_lookup_tool._implementation = item_lookup_impl
