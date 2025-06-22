"""
Shared utilities for tools
"""
import json
from datetime import datetime, date
from typing import Any, List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def format_date(date_input: Any) -> str:
    """Convert various date formats to YYYY-MM-DD"""
    if isinstance(date_input, str):
        # Try common formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y']:
            try:
                dt = datetime.strptime(date_input, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        # Return as-is if no format matches
        return date_input
    elif isinstance(date_input, (date, datetime)):
        return date_input.strftime('%Y-%m-%d')
    else:
        raise ValueError(f"Invalid date format: {date_input}")

def build_debug_sql(sql: str, params: List[Any]) -> str:
    """Build SQL string with parameters for debugging"""
    debug_sql = sql
    for param in params:
        if isinstance(param, str):
            value = f"'{param}'"
        elif isinstance(param, (date, datetime)):
            value = f"'{param}'"
        elif param is None:
            value = "NULL"
        else:
            value = str(param)
        
        debug_sql = debug_sql.replace('?', value, 1)
    
    return debug_sql

def format_currency(value: float) -> str:
    """Format as currency"""
    return f"${value:,.2f}"

def format_percentage(value: float, decimals: int = 1) -> str:
    """Format as percentage"""
    return f"{value * 100:.{decimals}f}%"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default for zero denominator"""
    if denominator == 0:
        return default
    return numerator / denominator

def create_tool_response(
    data: Any,
    sql: str,
    params: List[Any],
    metadata: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """Create standardized tool response"""
    response = {
        "data": data,
        "debug_sql": build_debug_sql(sql, params),
        "timestamp": datetime.now().isoformat(),
        "row_count": len(data) if isinstance(data, list) else 1
    }
    
    if metadata:
        response["metadata"] = metadata
    
    if error:
        response["error"] = error
        response["success"] = False
    else:
        response["success"] = True
    
    return response

def validate_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    """Validate and format date range"""
    start = format_date(start_date)
    end = format_date(end_date)
    
    # Validate dates
    start_dt = datetime.strptime(start, '%Y-%m-%d')
    end_dt = datetime.strptime(end, '%Y-%m-%d')
    
    if start_dt > end_dt:
        raise ValueError("Start date must be before or equal to end date")
    
    # Check reasonable range (e.g., max 1 year)
    if (end_dt - start_dt).days > 365:
        logger.warning(f"Large date range requested: {(end_dt - start_dt).days} days")
    
    return start, end