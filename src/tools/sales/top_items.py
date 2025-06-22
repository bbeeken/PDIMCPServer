"""Top selling items tool"""

from typing import Optional, Dict, Any
from mcp.types import Tool

from ...db.session import get_session
from ...repositories.sales_repository import SalesRepository
from ..utils import validate_date_range, create_tool_response


async def top_items_impl(
    start_date: str,
    end_date: str,
    metric: str = "sales",
    top_n: int = 10,
    site_id: Optional[int] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Return top selling items using various metrics"""
    start_date, end_date = validate_date_range(start_date, end_date)

    session = get_session()
    try:
        repo = SalesRepository(session)
        results = repo.top_items(
            start_date=start_date,
            end_date=end_date,
            metric=metric,
            top_n=top_n,
            site_id=site_id,
            category=category,
        )
        sql = "SalesRepository.top_items"
        params: list[Any] = []
        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "metric": metric,
            "top_n": top_n,
            "site_id": site_id,
            "category": category,
        }
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:
        return create_tool_response([], "SalesRepository.top_items", [], error=str(e))
    finally:
        session.close()


# Tool definition

top_items_tool = Tool(
    name="top_items",
    description="Get top selling items for a date range with optional filters",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "metric": {
                "type": "string",
                "enum": ["sales", "quantity", "transactions"],
                "description": "Metric to rank by",
                "default": "sales",
            },
            "top_n": {
                "type": "integer",
                "description": "Number of items to return",
                "default": 10,
            },
            "site_id": {"type": "integer", "description": "Optional site filter"},
            "category": {"type": "string", "description": "Optional category filter"},
        },
        "required": ["start_date", "end_date"],
    },
)

# Attach implementation

top_items_tool._implementation = top_items_impl
