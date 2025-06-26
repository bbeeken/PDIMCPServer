import importlib
import sys
import types
from .test_connection import load_connection


def load_server(monkeypatch):
    load_connection(monkeypatch)  # ensure db dependencies are stubbed

    # use real mcp; only stub tool modules

    # Stub tool modules used by src.mcp_server
    imports = [
        ("src.tools.sales.query_realtime", "query_sales_realtime_tool"),
        ("src.tools.sales.sales_summary", "sales_summary_tool"),
        ("src.tools.sales.sales_trend", "sales_trend_tool"),
        ("src.tools.sales.top_items", "top_items_tool"),
        ("src.tools.basket.basket_analysis", "basket_analysis_tool"),
        ("src.tools.basket.item_correlation", "item_correlation_tool"),
        ("src.tools.basket.cross_sell", "cross_sell_opportunities_tool"),
        ("src.tools.analytics.daily_report", "daily_report_tool"),
        ("src.tools.analytics.hourly_sales", "hourly_sales_tool"),
        ("src.tools.analytics.sales_gaps", "sales_gaps_tool"),
        ("src.tools.analytics.year_over_year", "year_over_year_tool"),
        ("src.tools.item_lookup", "item_lookup_tool"),
        ("src.tools.site_lookup", "site_lookup_tool"),
        ("src.tools.get_today_date", "get_today_date_tool"),
    ]

    from mcp.types import Tool

    for path, attr in imports:
        mod = types.ModuleType(path)
        tool = Tool(name=attr.replace("_tool", ""), description="", inputSchema={})
        setattr(mod, attr, tool)
        monkeypatch.setitem(sys.modules, path, mod)

    mcp_server = importlib.reload(importlib.import_module("src.mcp_server"))
    return mcp_server


def test_tool_registration(monkeypatch):
    mcp_server = load_server(monkeypatch)
    server = mcp_server.create_server()
    assert hasattr(server, "run")
    assert len(server.tools) == 14
    assert all(hasattr(t, "name") for t in server.tools)
