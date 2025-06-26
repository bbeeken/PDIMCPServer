import importlib
import sys
import types
from mcp.types import Tool

from fastapi.testclient import TestClient
from .test_connection import load_connection


def load_app(monkeypatch):
    load_connection(monkeypatch)

    # use real mcp; only stub tool modules

    imports = [
        ("src.tools.sales.query_realtime", "query_sales_realtime_tool"),
        ("src.tools.sales.sales_summary", "sales_summary_tool"),
        ("src.tools.sales.sales_trend", "sales_trend_tool"),
        ("src.tools.sales.top_items", "top_items_tool"),
        ("src.tools.basket.basket_analysis", "basket_analysis_tool"),
        ("src.tools.basket.item_correlation", "item_correlation_tool"),
        ("src.tools.basket.cross_sell", "cross_sell_opportunities_tool"),
        ("src.tools.basket.basket_metrics", "basket_metrics_tool"),
        ("src.tools.basket.transaction_lookup", "transaction_lookup_tool"),
        ("src.tools.analytics.daily_report", "daily_report_tool"),
        ("src.tools.analytics.hourly_sales", "hourly_sales_tool"),
        ("src.tools.analytics.peak_hours", "peak_hours_tool"),
        ("src.tools.analytics.sales_anomalies", "sales_anomalies_tool"),
        ("src.tools.analytics.product_velocity", "product_velocity_tool"),
        ("src.tools.analytics.low_movement", "low_movement_tool"),
        ("src.tools.analytics.daily_report", "daily_report_tool"),
        ("src.tools.analytics.sales_gaps", "sales_gaps_tool"),
        ("src.tools.analytics.year_over_year", "year_over_year_tool"),
        ("src.tools.item_lookup", "item_lookup_tool"),
        ("src.tools.site_lookup", "site_lookup_tool"),
        ("src.tools.get_today_date", "get_today_date_tool"),
    ]

    def make_impl(name):
        async def impl(**_kw):
            return {"result": name.replace("_tool", "")}

        return impl

    item_schema = importlib.import_module("src.tools.item_lookup").item_lookup_tool.inputSchema

    for path, attr in imports:
        mod = types.ModuleType(path)
        schema = item_schema if path == "src.tools.item_lookup" else {}
        tool = Tool(name=attr.replace("_tool", ""), description="", inputSchema=schema)
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
    assert len(resp.json()) == 20


def test_fastapi_call_tool(monkeypatch):
    app = load_app(monkeypatch)
    client = TestClient(app)
    resp = client.post("/sales_summary", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"] == "sales_summary"


def test_reject_unknown_parameters(monkeypatch):
    app = load_app(monkeypatch)
    client = TestClient(app)
    resp = client.post("/item_lookup", json={"item_id": 1, "bad": 1})
    assert resp.status_code == 422



def test_item_lookup_valid(monkeypatch):
    app = load_app(monkeypatch)
    client = TestClient(app)
    resp = client.post("/item_lookup", json={"item_id": 1})
    assert resp.status_code == 200


def test_transaction_lookup_call(monkeypatch):
    app = load_app(monkeypatch)
    client = TestClient(app)
    resp = client.post("/transaction_lookup", json={"transaction_id": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"] == "transaction_lookup"

def test_openapi_examples(monkeypatch):
    app = load_app(monkeypatch)
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    item_lookup_schema = (
        spec["paths"]["/item_lookup"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    )
    assert "example" in item_lookup_schema

