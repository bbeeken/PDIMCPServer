"""Lookup site information"""

from typing import Optional, Dict, Any
from mcp.types import Tool
from ..db.connection import execute_query
from .utils import create_tool_response


async def site_lookup_impl(
    site_id: Optional[int] = None,
    description: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Search ``dbo.Organization`` by site ID or description."""
    sql = """
    SELECT TOP (?)
        Site_id,
        Location_ID AS location_id,
        Location_Desc AS description,
        GPS_City,
        GPS_State,
        GPS_Latitude,
        GPS_Longitude
    FROM dbo.Organization
    WHERE 1=1
    """
    params = [limit]
    if site_id is not None:
        sql += " AND Site_id = ?"
        params.append(site_id)
    if description:
        sql += " AND Location_Desc LIKE ?"
        params.append(f"%{description}%")
    sql += " ORDER BY Location_Desc"
    try:
        results = execute_query(sql, params)
        metadata = {
            "filters": {"site_id": site_id, "description": description, "limit": limit}
        }
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - db errors depend on env
        return create_tool_response([], sql, params, error=str(e))


site_lookup_tool = Tool(
    name="site_lookup",
    description="Look up sites in dbo.Organization by ID or description",
    inputSchema={
        "type": "object",
        "properties": {
            "site_id": {"type": "integer", "description": "Exact site ID"},
            "description": {
                "type": "string",
                "description": "Partial site description",
            },
            "limit": {
                "type": "integer",
                "description": "Max rows to return",
                "default": 50,
            },
        },
        "required": [],
        "additionalProperties": False,
    },
)
site_lookup_tool._implementation = site_lookup_impl
