"""
Real-time sales query tool
"""
from typing import Optional, List, Dict, Any
from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response

async def query_sales_realtime_impl(
    start_date: str,
    end_date: str,
    item_name: Optional[str] = None,
    item_id: Optional[int] = None,
    site_id: Optional[int] = None,
    category: Optional[str] = None,
    min_amount: Optional[float] = None,
    limit: int = 1000
) -> Dict[str, Any]:
    """Query real-time sales data"""
    # Validate dates
    start_date, end_date = validate_date_range(start_date, end_date)
    
    # Build query
    sql = f"""
    SELECT TOP (?)
        TransactionID,
        SaleDate,
        DayOfWeek,
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
    WHERE SaleDate BETWEEN ? AND ?
    """
    
    params = [limit, start_date, end_date]
    
    # Add optional filters
    if item_id:
        sql += " AND ItemID = ?"
        params.append(item_id)
    elif item_name:
        sql += " AND ItemName LIKE ?"
        params.append(f"%{item_name}%")
    
    if site_id:
        sql += " AND SiteID = ?"
        params.append(site_id)
    
    if category:
        sql += " AND Category LIKE ?"
        params.append(f"%{category}%")
    
    if min_amount:
        sql += " AND GrossSales >= ?"
        params.append(min_amount)
    
    sql += " ORDER BY SaleDate DESC, TimeOfDay DESC"
    
    # Execute query
    try:
        results = execute_query(sql, params)
        
        # Convert time objects to strings
        for row in results:
            if 'TimeOfDay' in row and row['TimeOfDay']:
                row['TimeOfDay'] = str(row['TimeOfDay'])
            if 'SaleDate' in row and row['SaleDate']:
                row['SaleDate'] = str(row['SaleDate'])
        
        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "filters_applied": {
                "item_name": item_name,
                "item_id": item_id,
                "site_id": site_id,
                "category": category,
                "min_amount": min_amount
            }
        }
        
        return create_tool_response(results, sql, params, metadata)
        
    except Exception as e:
        return create_tool_response([], sql, params, error=str(e))

# Tool definition
query_sales_realtime_tool = Tool(
    name="query_sales_realtime",
    description="Query real-time sales transaction data with flexible filtering",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Start date (YYYY-MM-DD)"
            },
            "end_date": {
                "type": "string",
                "description": "End date (YYYY-MM-DD)"
            },
            "item_name": {
                "type": "string",
                "description": "Item name (partial match)"
            },
            "item_id": {
                "type": "integer",
                "description": "Exact item ID"
            },
            "site_id": {
                "type": "integer",
                "description": "Site ID filter"
            },
            "category": {
                "type": "string",
                "description": "Category filter (partial match)"
            },
            "min_amount": {
                "type": "number",
                "description": "Minimum sale amount"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum rows to return (default 1000)",
                "default": 1000
            }
        },
        "required": ["start_date", "end_date"]
    }
)

# Attach implementation to tool
query_sales_realtime_tool._implementation = query_sales_realtime_impl
