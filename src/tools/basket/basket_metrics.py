"""Basket metrics aggregation tool."""

from typing import Optional, List, Dict, Any

from mcp.types import Tool

from ...db.session import get_session
from ...repositories.basket_repository import BasketRepository
from ..utils import validate_date_range, create_tool_response


async def basket_metrics_impl(
    start_date: str,
    end_date: str,
    group_by: Optional[List[str]] = None,
    site_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Return aggregated basket metrics for the given date range."""
    start_date, end_date = validate_date_range(start_date, end_date)
    session = get_session()
    try:
        repo = BasketRepository(session)
        results = repo.basket_metrics(start_date, end_date, group_by, site_id)
        sql = "BasketRepository.basket_metrics"
        params: list[Any] = []
        metadata = {
            "date_range": f"{start_date} to {end_date}",
            "group_by": group_by,
            "site_id": site_id,
        }
        return create_tool_response(results, sql, params, metadata)
    except Exception as e:  # pragma: no cover - db errors depend on env
        return create_tool_response([], "BasketRepository.basket_metrics", [], error=str(e))
    finally:
        session.close()


basket_metrics_tool = Tool(
    name="basket_metrics",
    description="Calculate basket-level metrics like average value and size",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "group_by": {
                "type": "array",
                "items": {"type": "string", "enum": ["date", "site", "dayofweek"]},
                "description": "Dimensions to group results by",
            },
            "site_id": {"type": "integer", "description": "Optional site filter"},
        },
        "required": ["start_date", "end_date"],
    },
)

basket_metrics_tool._implementation = basket_metrics_impl

