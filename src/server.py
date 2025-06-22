"""
MCP Server implementation for PDI Sales Analytics
"""
import os
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .tools.sales.query_realtime import query_sales_realtime_tool
from .tools.sales.sales_summary import sales_summary_tool
from .tools.sales.sales_trend import sales_trend_tool
from .tools.sales.top_items import top_items_tool
from .tools.basket.basket_analysis import basket_analysis_tool
from .tools.basket.item_correlation import item_correlation_tool
from .tools.basket.cross_sell import cross_sell_opportunities_tool
from .tools.analytics.hourly_sales import hourly_sales_tool
from .tools.analytics.sales_gaps import sales_gaps_tool
from .tools.analytics.year_over_year import year_over_year_tool
from .tools.item_lookup import item_lookup_tool
from .tools.site_lookup import site_lookup_tool
from .tools.get_today_date import get_today_date_tool


logger = logging.getLogger(__name__)

# Server configuration
SERVER_NAME = os.getenv("MCP_SERVER_NAME", "mcp-pdi-sales")
SERVER_VERSION = os.getenv("MCP_SERVER_VERSION", "1.0.0")

async def main():
    """Main server entry point"""
    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    
    # Create server instance
    server = Server(SERVER_NAME)
    
    # Register all tools
    tools = [
        # Sales tools
        query_sales_realtime_tool,
        sales_summary_tool,
        sales_trend_tool,
        top_items_tool,

        # Basket analysis
        basket_analysis_tool,
        item_correlation_tool,
        cross_sell_opportunities_tool,

        # Analytics tools
        hourly_sales_tool,
        sales_gaps_tool,
        year_over_year_tool,

        # Utility tools
        item_lookup_tool,
        site_lookup_tool,
        get_today_date_tool,
    ]
    
    # Register handlers
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List all available tools"""
        logger.debug(f"Listing {len(tools)} tools")
        return tools
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]):
        """Execute a tool and return results as JSON"""
        logger.info(f"Calling tool: {name} with args: {arguments}")
        
        # Find the tool implementation
        tool_map = {tool.name: tool for tool in tools}
        
        if name not in tool_map:
            error_msg = f"Unknown tool: {name}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        try:
            # Get the tool's implementation function
            tool = tool_map[name]
            if hasattr(tool, '_implementation'):
                result = await tool._implementation(**arguments)
                return result
            else:
                error_msg = f"Tool {name} has no implementation"
                logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Error executing {name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}
    
    # Run the server
    logger.info("Server ready, starting stdio transport")
    await stdio_server(server, server_params={
        "server_name": SERVER_NAME,
        "server_version": SERVER_VERSION
    })

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
