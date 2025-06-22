"""MCP PDI Server - Main server implementation"""
from typing import List
from mcp.server import Server
from mcp.types import Tool

# Import all tools
from .tools.sales.query_realtime import query_sales_realtime_tool
from .tools.sales.sales_summary import sales_summary_tool
from .tools.sales.sales_trend import sales_trend_tool
from .tools.sales.top_items import top_items_tool

from .tools.basket.basket_analysis import basket_analysis_tool
from .tools.basket.item_correlation import item_correlation_tool
from .tools.basket.basket_metrics import basket_metrics_tool
from .tools.basket.cross_sell import cross_sell_opportunities_tool

from .tools.analytics.hourly_sales import hourly_sales_tool
from .tools.analytics.peak_hours import peak_hours_tool
from .tools.analytics.product_velocity import product_velocity_tool
from .tools.analytics.sales_anomalies import sales_anomalies_tool
from .tools.analytics.sales_gaps import sales_gaps_tool
from .tools.analytics.year_over_year import year_over_year_tool
from .tools.analytics.low_movement import low_movement_tool

from .tools.site_lookup import site_lookup_tool
from .tools.item_lookup import item_lookup_tool
from .tools.get_today_date import get_today_date_tool

def create_server() -> Server:
    """Create and configure the MCP server"""
    server = Server("mcp-pdi-sales")

    # Register all tools
    tools: List[Tool] = [
        # Sales tools
        query_sales_realtime_tool,
        sales_summary_tool,
        sales_trend_tool,
        top_items_tool,

        # Basket analysis tools
        basket_analysis_tool,
        item_correlation_tool,
        basket_metrics_tool,
        cross_sell_opportunities_tool,

        # Analytics tools
        hourly_sales_tool,
        peak_hours_tool,
        product_velocity_tool,
        sales_anomalies_tool,
        sales_gaps_tool,
        year_over_year_tool,
        low_movement_tool,

        # Lookup tools
        site_lookup_tool,
        item_lookup_tool,
        get_today_date_tool
    ]

    for tool in tools:
        server.add_tool(tool)

    return server

async def run_server():
    """Run the MCP server"""
    server = create_server()
    await server.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_server())
