from mcp.types import Tool

from .tools.sales.query_realtime import query_sales_realtime_tool
from .tools.sales.sales_summary import sales_summary_tool
from .tools.sales.sales_trend import sales_trend_tool
from .tools.sales.top_items import top_items_tool
from .tools.basket.basket_analysis import basket_analysis_tool
from .tools.basket.item_correlation import item_correlation_tool
from .tools.basket.cross_sell import cross_sell_opportunities_tool
from .tools.analytics.daily_report import daily_report_tool
from .tools.analytics.hourly_sales import hourly_sales_tool
from .tools.analytics.sales_gaps import sales_gaps_tool
from .tools.analytics.year_over_year import year_over_year_tool
from .tools.analytics.daily_report import daily_report_tool
from .tools.item_lookup import item_lookup_tool
from .tools.site_lookup import site_lookup_tool
from .tools.get_today_date import get_today_date_tool

TOOLS: list[Tool] = [
    query_sales_realtime_tool,
    sales_summary_tool,
    sales_trend_tool,
    top_items_tool,
    basket_analysis_tool,
    item_correlation_tool,
    cross_sell_opportunities_tool,
    daily_report_tool,
    hourly_sales_tool,
    daily_report_tool,
    sales_gaps_tool,
    year_over_year_tool,
    item_lookup_tool,
    site_lookup_tool,
    get_today_date_tool,
]
