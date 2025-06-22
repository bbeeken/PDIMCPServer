"""Lookup product details by item id or description."""

from typing import Optional, Dict, Any

from mcp.types import Tool

from ..db.connection import execute_query
from .utils import create_tool_response


async def item_lookup_impl(
    item_id: Optional[int] = None,
    description: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Query ``dbo.Product`` for matching items."""

    sql = """
    SELECT TOP (?)
        Item_ID AS item_id,
        Item_Desc AS description,
        Category_Desc AS category,
        Department_Desc AS department,
        UPC,
        Size_Desc AS size
    FROM dbo.Product
    WHERE 1=1
    """

    params = [limit]

    if item_id is not None:
        sql += " AND Item_ID = ?"
        params.append(item_id)

    if description:
        sql += " AND Item_Desc LIKE ?"
        params.append(f"%{description}%")

    sql += " ORDER BY Item_Desc"

    try:
        results = execute_query(sql, params)
        metadata = {"filters": {"item_id": item_id, "description": description, "limit": limit}}
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - database errors vary by environment
        return create_tool_response([], sql, params, error=str(e))


item_lookup_tool = Tool(
    name="item_lookup",
    description="Look up product information by item ID or description",
    inputSchema={
        "type": "object",
        "properties": {
            "item_id": {"type": "integer", "description": "Exact item ID"},
            "description": {"type": "string", "description": "Partial description filter"},
            "limit": {"type": "integer", "description": "Maximum rows to return", "default": 50},
        },
        "required": [],
    },
)

item_lookup_tool._implementation = item_lookup_impl

