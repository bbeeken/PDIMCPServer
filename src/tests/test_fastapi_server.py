import importlib
import sys
import types

from fastapi.testclient import TestClient
from .test_connection import load_connection


def load_app(monkeypatch):
    load_connection(monkeypatch)

    # stub mcp.types Tool and TextContent
    mcp_mod = types.ModuleType("mcp")
    types_mod = types.ModuleType("mcp.types")

    class Tool:
        def __init__(self, name=""):
            self.name = name

    class TextContent:
        def __init__(self, type="text", text=""):
            self.type = type
            self.text = text

    types_mod.Tool = Tool
    types_mod.TextContent = TextContent
    mcp_mod.types = types_mod

    monkeypatch.setitem(sys.modules, "mcp", mcp_mod)
    monkeypatch.setitem(sys.modules, "mcp.types", types_mod)

    imports = [
        ("src.tools.sales.query_realtime", "query_sales_realtime_tool"),
        ("src.tools.sales.sales_summary", "sales_summary_tool"),
        ("src.tools.sales.sales_trend", "sales_trend_tool"),
        ("src.tools.sales.top_items", "top_items_tool"),
        ("src.tools.basket.basket_analysis", "basket_analysis_tool"),
        ("src.tools.basket.item_correlation", "item_correlation_tool"),
        ("src.tools.basket.cross_sell", "cross_sell_opportunities_tool"),
        ("src.tools.analytics.hourly_sales", "hourly_sales_tool"),
        ("src.tools.analytics.sales_gaps", "sales_gaps_tool"),
        ("src.tools.analytics.year_over_year", "year_over_year_tool"),
        ("src.tools.item_lookup", "item_lookup_tool"),
        ("src.tools.site_lookup", "site_lookup_tool"),
        ("src.tools.get_today_date", "get_today_date_tool"),
    ]

    def make_impl(name):
        async def impl(**_kw):
            return {"result": name}

        return impl

    for path, attr in imports:
        mod = types.ModuleType(path)
        tool = Tool(name=attr)
        tool._implementation = make_impl(attr)
        setattr(mod, attr, tool)
        monkeypatch.setitem(sys.modules, path, mod)

    fastapi_server = importlib.reload(importlib.import_module("src.fastapi_server"))
    return fastapi_server.create_app()


def test_fastapi_list_tools(monkeypatch):
    app = load_app(monkeypatch)
    client = TestClient(app)
    resp = client.get("/tools")
    assert resp.status_code == 200
    assert len(resp.json()) == 13


def test_fastapi_call_tool(monkeypatch):
    app = load_app(monkeypatch)
    client = TestClient(app)
    resp = client.post("/call", json={"name": "sales_summary_tool", "arguments": {}})
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"] == "sales_summary_tool"
