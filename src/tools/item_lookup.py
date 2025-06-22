"""Lookup product information"""
from typing import Optional, Dict, Any
from mcp.types import Tool
from .utils import create_tool_response
from ..db.connection import execute_query


async def item_lookup_impl(
    item_id: Optional[int] = None,
    description: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """Search dbo.Product by item ID or description."""
    sql = """
    SELECT TOP (?)
        Item_ID,
        Item_Desc,
        Category_Desc,
        Department_Desc,
        UPC,
        Size_Desc
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
    except Exception as e:  # pragma: no cover - database errors depend on env
        return create_tool_response([], sql, params, error=str(e))


item_lookup_tool = Tool(
    name="item_lookup",
    description="Look up items in dbo.Product by ID or description",
    inputSchema={
        "type": "object",
        "properties": {
            "item_id": {"type": "integer", "description": "Exact item ID"},
            "description": {"type": "string", "description": "Partial item description"},
            "limit": {"type": "integer", "description": "Max rows to return", "default": 20},
        },
    },
)

item_lookup_tool._implementation = item_lookup_impl
