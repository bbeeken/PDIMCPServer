"""Item correlation analysis tool"""

from typing import Dict, Any, Optional
from mcp.types import Tool
from ...db.session import get_db
from ..utils import format_date, format_response, execute_sql


async def item_correlation_impl(
    item_id: int,
    start_date: str,
    end_date: str,
    min_frequency: int = 5,
    top_n: int = 20,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Find items frequently bought with a specific item"""
    query = """
    WITH TargetTransactions AS (
        SELECT DISTINCT TransactionID
        FROM dbo.V_LLM_SalesFact
        WHERE ItemID = :item_id
            AND SaleDate BETWEEN :start_date AND :end_date
    """
    params = {
        "item_id": item_id,
        "start_date": format_date(start_date),
        "end_date": format_date(end_date),
        "min_frequency": min_frequency,
        "top_n": top_n,
    }
    if site_id:
        query += " AND SiteID = :site_id"
        params["site_id"] = site_id
    query += """
    ),
    TargetInfo AS (
        SELECT TOP 1 ItemName, Category
        FROM dbo.V_LLM_SalesFact
        WHERE ItemID = :item_id
    ),
    Correlations AS (
        SELECT
            s.ItemID, s.ItemName, s.Category,
            COUNT(DISTINCT s.TransactionID) AS co_occurrence_count,
            AVG(s.QtySold) AS avg_qty_together,
            AVG(s.GrossSales) AS avg_sales_together,
            SUM(s.QtySold) AS total_qty_together,
            SUM(s.GrossSales) AS total_sales_together
        FROM dbo.V_LLM_SalesFact s
        JOIN TargetTransactions t ON s.TransactionID = t.TransactionID
        WHERE s.ItemID != :item_id
    """
    if site_id:
        query += " AND s.SiteID = :site_id"
    query += """
        GROUP BY s.ItemID, s.ItemName, s.Category
        HAVING COUNT(DISTINCT s.TransactionID) >= :min_frequency
    )
    SELECT TOP (:top_n)
        ti.ItemName AS target_item_name,
        ti.Category AS target_category,
        (SELECT COUNT(*) FROM TargetTransactions) AS target_transaction_count,
        c.ItemID, c.ItemName, c.Category,
        c.co_occurrence_count,
        ROUND(CAST(c.co_occurrence_count AS FLOAT) / 
              (SELECT COUNT(*) FROM TargetTransactions), 3) AS confidence,
        c.avg_qty_together, c.avg_sales_together,
        c.total_qty_together, c.total_sales_together
    FROM Correlations c
    CROSS JOIN TargetInfo ti
    ORDER BY c.co_occurrence_count DESC
    """
    try:
        with get_db() as db:
            data = execute_sql(db, query, params)
            if not data:
                return format_response(
                    success=True,
                    data=[],
                    debug_sql=query,
                    metadata={
                        "target_item": {"id": item_id},
                        "message": "No correlations found",
                    },
                )
            target_info = {
                "id": item_id,
                "name": data[0]["target_item_name"],
                "category": data[0]["target_category"],
                "transaction_count": data[0]["target_transaction_count"],
            }
            correlations = []
            for row in data:
                correlations.append(
                    {
                        "item": {
                            "id": row["ItemID"],
                            "name": row["ItemName"],
                            "category": row["Category"],
                        },
                        "metrics": {
                            "co_occurrence_count": row["co_occurrence_count"],
                            "confidence": row["confidence"],
                        },
                        "purchase_behavior": {
                            "avg_qty_together": round(
                                float(row["avg_qty_together"]), 2
                            ),
                            "avg_sales_together": round(
                                float(row["avg_sales_together"]), 2
                            ),
                            "total_qty_together": round(
                                float(row["total_qty_together"]), 2
                            ),
                            "total_sales_together": round(
                                float(row["total_sales_together"]), 2
                            ),
                        },
                    }
                )
            return format_response(
                success=True,
                data=correlations,
                debug_sql=query,
                metadata={
                    "target_item": target_info,
                    "parameters": {
                        "date_range": f"{start_date} to {end_date}",
                        "min_frequency": min_frequency,
                        "site_id": site_id,
                    },
                },
            )
    except Exception as e:
        return format_response(success=False, data=[], debug_sql=query, error=str(e))


item_correlation_tool = Tool(
    name="item_correlation",
    description=(
        "Analyse transactions containing a target item and identify other items "
        "that commonly appear in the same basket. Useful for bundle planning."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "item_id": {"type": "integer", "description": "Target item ID"},
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "min_frequency": {
                "type": "integer",
                "description": "Minimum co-occurrence count",
            },
            "top_n": {"type": "integer", "description": "Number of correlated items"},
            "site_id": {"type": "integer", "description": "Filter by site ID"},
        },
        "required": ["item_id", "start_date", "end_date"],
        "additionalProperties": False,
    },
)
item_correlation_tool._implementation = item_correlation_impl
