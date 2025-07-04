"""Enhanced product lookup with multi-token fuzzy search.

This tool queries **PDI_Warehouse_1539_01.dbo.product_view** and supports:
• Exact *item_id* match
• Multi-token *description* search (any word order, case-insensitive)
• Excludes brands marked **UNAUTH** / **DEAUTH**

Examples
--------
>>> item_lookup(description="20oz coke")
# will match "COKE CLASSIC 20 OZ" etc.
"""

from __future__ import annotations

import re
from typing import Optional, Dict, Any, List

from mcp.types import Tool

from ..db.connection import execute_query
from .utils import create_tool_response

# ────────────────────────────────────────────────────────────────
# Implementation
# ────────────────────────────────────────────────────────────────

async def item_lookup_impl(  # noqa: N802 – fixed by framework
    item_id: Optional[int] = None,
    description: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Search **product_view** by *item_id* or *description*.

    Parameters
    ----------
    item_id: int | None
        Exact `Item_ID` to match.
    description: str | None
        One or more words describing the product (word order insensitive).
    limit: int
        Maximum rows to return.
    """

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
        WHERE  1 = 1
          AND  UPPER(Brand) NOT LIKE '%UNAUTH%'
          AND  UPPER(Brand) NOT LIKE '%DEAUTH%'
        """
    )
    params: List[Any] = [limit]

    # ── Exact ID filter ─────────────────────────────────────────
    if item_id is not None:
        sql += " AND Item_ID = ?"
        params.append(item_id)

    # ── Multi-token description filter ──────────────────────────
    if description:
        # Split on whitespace & punctuation, drop empty tokens
        tokens = [t.upper() for t in re.split(r"[\s,.;:-]+", description) if t]
        for token in tokens:
            sql += " AND UPPER(Item_Desc) LIKE ?"
            params.append(f"%{token}%")

    sql += " ORDER BY Item_Desc"

    # ── Execute query ───────────────────────────────────────────
    try:
        results = execute_query(sql, params)
        metadata = {
            "filters": {
                "item_id": item_id,
                "description": description,
                "tokens": tokens if description else [],
                "limit": limit,
            }
        }
        return create_tool_response(results, sql, params, metadata)
    except Exception as exc:  # pragma: no cover – DB-specific errors
        return create_tool_response([], sql, params, error=str(exc))


# ────────────────────────────────────────────────────────────────
# Tool registration
# ────────────────────────────────────────────────────────────────

item_lookup_tool = Tool(
    name="item_lookup",
    description=(
        "Look up authorised items in **product_view** by ID or description. "
        "The *description* search splits the query into words and matches "
        "each word (case-insensitive, any order), e.g. ‘20oz coke’ ⇒ "
        "‘COKE 20 OZ’."
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
                "description": "Free-text description (word order insensitive)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of rows to return",
                "default": 50,
            },
        },
        "required": [],
        "additionalProperties": False,
    },
)


# Attach implementation
item_lookup_tool._implementation = item_lookup_impl

