"""Simple utility to get today's date"""
from datetime import date
from typing import Dict, Any
from mcp.types import Tool

async def get_today_date_impl() -> Dict[str, Any]:
    return {"date": date.today().isoformat(), "success": True}

get_today_date_tool = Tool(
    name="get_today_date",
    description="Get today's date in YYYY-MM-DD format",
    inputSchema={"type": "object", "properties": {}, "required": []}
)
get_today_date_tool._implementation = get_today_date_impl
