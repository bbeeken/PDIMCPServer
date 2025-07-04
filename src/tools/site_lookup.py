# src/tools/site_lookup.py
# Fully-cleaned – aligned to dbo.V_LLM_Sites and **no** duplicate blocks

from __future__ import annotations
from typing import Optional, Dict, Any

from mcp.types import Tool
from ..db.connection import execute_query
from .utils import create_tool_response


# ────────────────────────────────────────────────────────────────
# Implementation
# ────────────────────────────────────────────────────────────────
async def site_lookup_impl(
    site_id: Optional[int | str] = None,
    description: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Look up rows in **dbo.V_LLM_Sites**.

    • `site_id`  > 0 → exact Site_id match
    • `site_id`  0 / None / "" → no Site_id filter (all sites)
    • `description` finds partial matches in Site_desc, GPS_City, or GPS_State.
    """

    # ── Base query ------------------------------------------------------
    sql = """
    SELECT TOP (:limit)
           Site_id        AS SiteID,
           Site_desc      AS SiteName,
           GPS_Address1   AS Address,
           GPS_City       AS City,
           GPS_State      AS State,
           GPS_Zip        AS PostalCode,
           TimeZone_ID    AS TimeZone,
           GPS_Longitude  AS Longitude,
           GPS_Latitude   AS Latitude
    FROM   dbo.V_LLM_Sites
    WHERE  1 = 1
    """
    params: Dict[str, Any] = {"limit": limit}

    # Site-ID filter
    try:
        sid = int(site_id) if site_id not in (None, "", "0") else 0
    except (TypeError, ValueError):
        sid = 0
    if sid > 0:
        sql += " AND Site_id = :site_id"
        params["site_id"] = sid

    # Description filter
    if description:
        sql += """
        AND (
                 Site_desc LIKE :desc
              OR GPS_City  LIKE :desc
              OR GPS_State LIKE :desc
            )
        """
        params["desc"] = f"%{description}%"

    sql += " ORDER BY Site_desc"

    # ── Execute ---------------------------------------------------------
    try:
        rows = execute_query(sql, params)
        meta = {
            "filters": {
                "site_id": sid if sid > 0 else None,
                "description": description,
                "limit": limit,
            }
        }
        return create_tool_response(rows, sql, params, meta)

    except Exception as exc:  # pragma: no cover – db-env specific
        return create_tool_response([], sql, params, error=str(exc))


# ────────────────────────────────────────────────────────────────
# Tool registration
# ────────────────────────────────────────────────────────────────
site_lookup_tool = Tool(
    name="site_lookup",
    description=(
        "Retrieve site information from dbo.V_LLM_Sites. Supports filtering by "
        "exact Site_id or by partial name, city or state and returns address, "
        "coordinates and timezone."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "site_id": {
                "type": "integer",
                "minimum": 0,
                "default": 0,
                "description": "Exact Site_id; 0 = all sites",
            },
            "description": {
                "type": "string",
                "description": "Partial match on Site_desc / City / State",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 500,
                "default": 50,
                "description": "Maximum rows to return",
            },
        },
        "required": [],
        "additionalProperties": False,
    },
)
site_lookup_tool._implementation = site_lookup_impl
