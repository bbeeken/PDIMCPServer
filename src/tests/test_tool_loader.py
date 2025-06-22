import logging
import httpx

from src.tool_loader import load_tools


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self) -> None:
        pass

    def json(self):
        return self._data


def test_load_tools_success(monkeypatch):
    fake_tools = [{"name": "a"}, {"name": "b"}]

    def fake_get(url, timeout=10):
        return DummyResponse(fake_tools)

    monkeypatch.setattr(httpx, "get", fake_get)
    assert load_tools("http://example.com") == fake_tools


def test_load_tools_failure(monkeypatch, caplog):
    def fake_get(url, timeout=10):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(httpx, "get", fake_get)
    with caplog.at_level(logging.ERROR):
        result = load_tools("http://example.com")
    assert result is None
    assert any("boom" in rec.getMessage() for rec in caplog.records)
