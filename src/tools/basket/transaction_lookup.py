"""Lookup all line items for a transaction"""

from typing import Any, Dict, Optional
from mcp.types import Tool

from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import create_tool_response


async def transaction_lookup_impl(
    transaction_id: int,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Return all rows from ``V_LLM_SalesFact`` matching ``transaction_id``."""
    sql = f"""
    SELECT
        TransactionID,
        LineItemNumber,
        SaleDate,
        TimeOfDay,
        SiteID,
        SiteName,
        ItemID,
        ItemName,
        Category,
        Department,
        QtySold,
        Price,
        GrossSales
    FROM {SALES_FACT_VIEW}
    WHERE TransactionID = :transaction_id
    """
    params: Dict[str, Any] = {"transaction_id": transaction_id}
    if site_id is not None:
        sql += " AND SiteID = :site_id"
        params["site_id"] = site_id
    sql += " ORDER BY LineItemNumber"

    try:
        results = execute_query(sql, params)
        for row in results:
            if "SaleDate" in row and row["SaleDate"] is not None:
                row["SaleDate"] = str(row["SaleDate"])
            if "TimeOfDay" in row and row["TimeOfDay"] is not None:
                row["TimeOfDay"] = str(row["TimeOfDay"])
        metadata = {"transaction_id": transaction_id, "site_id": site_id}
        return create_tool_response(results, sql, params, metadata)
    except Exception as exc:  # pragma: no cover - depends on DB state
        return create_tool_response([], sql, params, error=str(exc))


transaction_lookup_tool = Tool(
    name="transaction_lookup",
    description=(
        "Retrieve all line items belonging to a transaction ID. "
        "Optionally filter by site_id to ensure results come from a single location."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "transaction_id": {
                "type": "integer",
                "description": "TransactionID to lookup",
            },
            "site_id": {"type": "integer", "description": "Optional site filter"},
        },
        "required": ["transaction_id"],
        "additionalProperties": False,
    },
)
transaction_lookup_tool._implementation = transaction_lookup_impl
