import importlib
import sys
import types
from .test_connection import load_connection


def load_server(monkeypatch):
    load_connection(monkeypatch)  # ensure db dependencies are stubbed

    # Stub MCP server and Tool classes
    mcp_mod = types.ModuleType("mcp")
    server_mod = types.ModuleType("mcp.server")
    types_mod = types.ModuleType("mcp.types")

    class DummyServer:
        def __init__(self, name):
            self.name = name
            self.tools = []

        def add_tool(self, tool):
            self.tools.append(tool)

    class Tool:
        def __init__(self, name="", description="", inputSchema=None):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema or {}

    server_mod.Server = DummyServer
    types_mod.Tool = Tool
    mcp_mod.server = server_mod
    mcp_mod.types = types_mod

    monkeypatch.setitem(sys.modules, "mcp", mcp_mod)
    monkeypatch.setitem(sys.modules, "mcp.server", server_mod)
    monkeypatch.setitem(sys.modules, "mcp.types", types_mod)

    # Stub tool modules used by src.mcp_server
    imports = [
        ("src.tools.sales.query_realtime", "query_sales_realtime_tool"),
        ("src.tools.sales.sales_summary", "sales_summary_tool"),
        ("src.tools.sales.sales_trend", "sales_trend_tool"),
        ("src.tools.sales.top_items", "top_items_tool"),
        ("src.tools.basket.basket_analysis", "basket_analysis_tool"),
        ("src.tools.basket.item_correlation", "item_correlation_tool"),
        ("src.tools.basket.basket_metrics", "basket_metrics_tool"),
        ("src.tools.basket.cross_sell", "cross_sell_tool"),
        ("src.tools.analytics.hourly_sales", "hourly_sales_tool"),
        ("src.tools.analytics.peak_hours", "peak_hours_tool"),
        ("src.tools.analytics.product_velocity", "product_velocity_tool"),
        ("src.tools.analytics.sales_anomalies", "sales_anomalies_tool"),
        ("src.tools.analytics.sales_gaps", "sales_gaps_tool"),
        ("src.tools.analytics.year_over_year", "year_over_year_tool"),
        ("src.tools.analytics.low_movement", "low_movement_tool"),
        ("src.tools.site_lookup", "site_lookup_tool"),
        ("src.tools.item_lookup", "item_lookup_tool"),
        ("src.tools.get_today_date", "get_today_date_tool"),
    ]

    for path, attr in imports:
        mod = types.ModuleType(path)
        tool = Tool(name=attr)
        setattr(mod, attr, tool)
        monkeypatch.setitem(sys.modules, path, mod)

    mcp_server = importlib.reload(importlib.import_module("src.mcp_server"))
    return mcp_server, DummyServer


def test_tool_registration(monkeypatch):
    mcp_server, DummyServer = load_server(monkeypatch)
    server = mcp_server.create_server()
    assert isinstance(server, DummyServer)
    assert len(server.tools) == 18
    assert all(hasattr(t, "name") for t in server.tools)
