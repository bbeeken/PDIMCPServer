"""
Shared utilities for tools
"""

from datetime import datetime, date
from typing import Any, List, Dict, Optional, Union
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


def format_date(date_input: Any) -> str:
    """Convert various date formats to YYYY-MM-DD"""
    if isinstance(date_input, str):
        # Try common formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"]:
            try:
                dt = datetime.strptime(date_input, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        # If no format matches raise an error
        raise ValueError(f"Invalid date format: {date_input}. Expected YYYY-MM-DD")
    elif isinstance(date_input, (date, datetime)):
        return date_input.strftime("%Y-%m-%d")
    else:
        raise ValueError(f"Invalid date format: {date_input}")


def build_debug_sql(sql: str, params: Union[List[Any], Dict[str, Any]]) -> str:
    """Build SQL string with parameters for debugging"""
    debug_sql = sql
    if isinstance(params, dict):
        for key, param in params.items():
            if isinstance(param, str):
                value = f"'{param}'"
            elif isinstance(param, (date, datetime)):
                value = f"'{param}'"
            elif param is None:
                value = "NULL"
            else:
                value = str(param)
            debug_sql = debug_sql.replace(f":{key}", value)
    else:
        for param in params:
            if isinstance(param, str):
                value = f"'{param}'"
            elif isinstance(param, (date, datetime)):
                value = f"'{param}'"
            elif param is None:
                value = "NULL"
            else:
                value = str(param)
            debug_sql = debug_sql.replace("?", value, 1)
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
    params: Union[List[Any], Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Create standardized tool response"""
    response = {
        "data": data,
        "debug_sql": build_debug_sql(sql, params),
        "timestamp": datetime.now().isoformat(),
        "row_count": len(data) if isinstance(data, list) else 1,
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
    try:
        start = format_date(start_date)
        end = format_date(end_date)
    except ValueError as exc:
        raise ValueError(f"Invalid date range: {exc}") from exc

    # Validate dates
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")

    if start_dt > end_dt:
        raise ValueError("Start date must be before or equal to end date")

    # Check reasonable range (e.g., max 1 year)
    if (end_dt - start_dt).days > 365:
        logger.warning(f"Large date range requested: {(end_dt - start_dt).days} days")

    return start, end


def format_response(
    success: bool,
    data: Any,
    debug_sql: str,
    metadata: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a response dictionary for older basket tools."""

    response = {
        "success": success,
        "data": data,
        "debug_sql": debug_sql,
        "timestamp": datetime.now().isoformat(),
        "row_count": len(data) if isinstance(data, list) else 1,
    }

    if metadata:
        response["metadata"] = metadata

    if error:
        response["error"] = error

    return response


def execute_sql(
    db_session, sql: str, params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Execute a SQL statement using an SQLAlchemy session."""

    result = db_session.execute(text(sql), params or {})
    rows = result.fetchall()
    columns = result.keys()

    return [dict(zip(columns, row)) for row in rows]
