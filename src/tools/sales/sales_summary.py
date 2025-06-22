"""
Sales summary tool
"""

from typing import Optional, List, Dict, Any
from mcp.types import Tool
from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response


async def sales_summary_impl(
    start_date: str,
    end_date: str,
    group_by: Optional[List[str]] = None,
    site_id: Optional[int] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate sales summary with optional grouping"""
    start_date, end_date = validate_date_range(start_date, end_date)

    # Default grouping
    if group_by is None:
        group_by = []

    # Map grouping options
    group_mapping = {
        "date": "SaleDate",
        "site": "SiteID, SiteName",
        "category": "Category",
        "department": "Department",
        "dayofweek": "DayOfWeek",
    }

    # Build SELECT and GROUP BY
    select_cols = []
    group_cols = []

    for g in group_by:
        if g in group_mapping:
            cols = group_mapping[g].split(", ")
            select_cols.extend(cols)
            group_cols.extend(cols)

    # Build query
    if select_cols:
        select_part = ", ".join(select_cols) + ", "
        group_part = "GROUP BY " + ", ".join(group_cols)
    else:
        select_part = ""
        group_part = ""

    sql = f"""
    SELECT 
        {select_part}
        COUNT(DISTINCT TransactionID) as TransactionCount,
        COUNT(DISTINCT ItemID) as UniqueItems,
        SUM(QtySold) as TotalQuantity,
        SUM(GrossSales) as TotalSales,
        AVG(GrossSales) as AvgSaleAmount
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN ? AND ?
    """

    params = [start_date, end_date]

    if site_id:
        sql += " AND SiteID = ?"
        params.append(site_id)

    if category:
        sql += " AND Category LIKE ?"
        params.append(f"%{category}%")

    sql += f" {group_part}"

    if select_cols:
        sql += " ORDER BY " + select_cols[0]

    try:
        results = execute_query(sql, params)

        # Format dates in results
        for row in results:
            if "SaleDate" in row and row["SaleDate"]:
                row["SaleDate"] = str(row["SaleDate"])

        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "grouping": group_by if group_by else "overall",
            "filters": {"site_id": site_id, "category": category},
        }

        return create_tool_response(results, sql, params, metadata)

    except Exception as e:
        return create_tool_response([], sql, params, error=str(e))


# Tool definition
sales_summary_tool = Tool(
    name="sales_summary",
    description="Generate sales summary with flexible grouping options",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "group_by": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["date", "site", "category", "department", "dayofweek"],
                },
                "description": "Grouping dimensions",
            },
            "site_id": {"type": "integer", "description": "Optional site filter"},
            "category": {"type": "string", "description": "Optional category filter"},
        },
        "required": ["start_date", "end_date"],
    },
)

sales_summary_tool._implementation = sales_summary_impl
