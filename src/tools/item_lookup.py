"""Lookup product information"""

from typing import Optional, Dict, Any
from mcp.types import Tool
from ..db.connection import execute_query
from .utils import create_tool_response


async def item_lookup_impl(
    item_id: Optional[int] = None,
    description: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Search ``dbo.Product`` by item ID or description."""
    sql = """
    SELECT TOP (:limit)
        Item_ID AS item_id,
        Item_Desc AS description,
        Category_Desc AS category,
        Department_Desc AS department,
        UPC,
        Size_Desc AS size
    FROM dbo.Product
    WHERE 1=1
    """
    params = {"limit": limit}
    if item_id is not None:
        sql += " AND Item_ID = :item_id"
        params["item_id"] = item_id
    if description:
        sql += " AND Item_Desc LIKE :description"
        params["description"] = f"%{description}%"
    sql += " ORDER BY Item_Desc"
    try:
        results = execute_query(sql, params)
        metadata = {
            "filters": {"item_id": item_id, "description": description, "limit": limit}
        }
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - db errors depend on env
        return create_tool_response([], sql, params, error=str(e))


item_lookup_tool = Tool(
    name="item_lookup",
    description=(
        "Search dbo.Product by item ID or partial description to retrieve "
        "category, department, UPC and size details."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "item_id": {"type": "integer", "description": "Exact item ID"},
            "description": {
                "type": "string",
                "description": "Partial item description",
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
item_lookup_tool._implementation = item_lookup_impl
