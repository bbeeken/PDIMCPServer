"""
Sales trend analysis tool
"""
from typing import Optional, Dict, Any
from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response

async def sales_trend_impl(
    start_date: str,
    end_date: str,
    interval: str = "daily",
    site_id: Optional[int] = None,
    category: Optional[str] = None,
    metric: str = "sales"
) -> Dict[str, Any]:
    """Analyze sales trends over time"""
    start_date, end_date = validate_date_range(start_date, end_date)
    
    # Map interval to SQL
    interval_mapping = {
        'daily': 'SaleDate',
        'weekly': "DATEPART(WEEK, SaleDate) as Week, DATEPART(YEAR, SaleDate) as Year",
        'monthly': "DATEPART(MONTH, SaleDate) as Month, DATEPART(YEAR, SaleDate) as Year",
        'hourly': "SaleDate, DATEPART(HOUR, TimeOfDay) as Hour"
    }
    
    if int