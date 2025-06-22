"""Market basket analysis tool"""

from typing import Dict, Any, Optional
from mcp.types import Tool
from ...db.session import get_db
from ..utils import format_date, format_response, execute_sql


async def basket_analysis_impl(
    start_date: str,
    end_date: str,
    min_support: float = 0.01,
    min_confidence: float = 0.5,
    site_id: Optional[int] = None,
    max_items: int = 50,
) -> Dict[str, Any]:
    """Find frequently bought together items with lift analysis"""
    query = """
    WITH TxItems AS (
        SELECT DISTINCT TransactionID, ItemID, ItemName
        FROM dbo.V_LLM_SalesFact
        WHERE SaleDate BETWEEN :start_date AND :end_date
    """
    params = {
        "start_date": format_date(start_date),
        "end_date": format_date(end_date),
        "max_items": max_items,
    }
    if site_id:
        query += " AND SiteID = :site_id"
        params["site_id"] = site_id
    query += """
    ),
    TxCount AS (
        SELECT COUNT(DISTINCT TransactionID) AS total_transactions
        FROM dbo.V_LLM_SalesFact
        WHERE SaleDate BETWEEN :start_date AND :end_date
    """
    if site_id:
        query += " AND SiteID = :site_id"
    query += """
    ),
    ItemSupport AS (
        SELECT ItemID, ItemName, COUNT(DISTINCT TransactionID) AS support_count
        FROM TxItems
        GROUP BY ItemID, ItemName
    ),
    ItemPairs AS (
        SELECT
            a.ItemID AS item1_id,
            a.ItemName AS item1_name,
            b.ItemID AS item2_id,
            b.ItemName AS item2_name,
            COUNT(DISTINCT a.TransactionID) AS pair_count
        FROM TxItems a
        JOIN TxItems b ON a.TransactionID = b.TransactionID AND a.ItemID < b.ItemID
        GROUP BY a.ItemID, a.ItemName, b.ItemID, b.ItemName
    )
    SELECT TOP (:max_items)
        p.item1_id, p.item1_name,
        p.item2_id, p.item2_name,
        p.pair_count,
        t.total_transactions,
        s1.support_count AS item1_count,
        s2.support_count AS item2_count,
        CAST(p.pair_count AS FLOAT)/t.total_transactions AS support,
        CAST(p.pair_count AS FLOAT)/s1.support_count AS confidence,
        ROUND(
            (CAST(p.pair_count AS FLOAT) * t.total_transactions) /
            (s1.support_count * s2.support_count), 2) AS lift
    FROM ItemPairs p
    CROSS JOIN TxCount t
    JOIN ItemSupport s1 ON p.item1_id = s1.ItemID
    JOIN ItemSupport s2 ON p.item2_id = s2.ItemID
    WHERE
        CAST(p.pair_count AS FLOAT)/t.total_transactions >= :min_support
        AND CAST(p.pair_count AS FLOAT)/s1.support_count >= :min_confidence
    ORDER BY lift DESC
    """
    params["min_support"] = min_support
    params["min_confidence"] = min_confidence

    try:
        with get_db() as db:
            data = execute_sql(db, query, params)
            results = []
            for row in data:
                results.append(
                    {
                        "item1": {"id": row["item1_id"], "name": row["item1_name"]},
                        "item2": {"id": row["item2_id"], "name": row["item2_name"]},
                        "metrics": {
                            "support": round(row["support"], 4),
                            "confidence": round(row["confidence"], 3),
                            "lift": row["lift"],
                            "frequency": row["pair_count"],
                        },
                    }
                )
            return format_response(
                success=True,
                data=results,
                debug_sql=query,
                metadata={
                    "parameters": {
                        "min_support": min_support,
                        "min_confidence": min_confidence,
                        "date_range": f"{start_date} to {end_date}",
                        "site_id": site_id,
                    }
                },
            )
    except Exception as e:
        return format_response(success=False, data=[], debug_sql=query, error=str(e))


basket_analysis_tool = Tool(
    name="basket_analysis",
    description="Find frequently bought together items with support, confidence, and lift metrics",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "min_support": {
                "type": "number",
                "description": "Minimum support threshold",
            },
            "min_confidence": {
                "type": "number",
                "description": "Minimum confidence threshold",
            },
            "site_id": {"type": "integer", "description": "Filter by site ID"},
            "max_items": {"type": "integer", "description": "Maximum pairs to return"},
        },
        "required": ["start_date", "end_date"],
    },
)
basket_analysis_tool._implementation = basket_analysis_impl
