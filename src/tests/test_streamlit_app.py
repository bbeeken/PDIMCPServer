import importlib
import sys
import types

import pytest


@pytest.fixture
def sa_module(monkeypatch):
    calls = []
    st = types.ModuleType("streamlit")

    def record(name, ret=None):
        def fn(*args, **kwargs):
            calls.append((name, args, kwargs))
            return ret
        return fn

    st.checkbox = record("checkbox", False)
    st.cache_data = lambda fn: fn
    st.dataframe = record("dataframe")
    st.line_chart = record("line_chart")
    st.bar_chart = record("bar_chart")
    st.download_button = record("download_button")
    st.text = record("text")
    st.json = record("json")

    pd = types.ModuleType("pandas")

    class DF:
        def __init__(self):
            self.columns = ["a"]

        def select_dtypes(self, *a, **k):
            return self

        def to_csv(self, index=False):
            return "csv"

    pd.DataFrame = lambda data: calls.append(("DataFrame", data)) or DF()

    monkeypatch.setitem(sys.modules, "streamlit", st)
    monkeypatch.setitem(sys.modules, "pandas", pd)

    sa = importlib.reload(importlib.import_module("streamlit_app"))
    calls.clear()
    return sa, calls, st


def test_render_content_table(sa_module):
    sa, calls, st = sa_module
    sa.render_content({"type": "text", "text": "[{\"a\":1}]"}, 0)
    assert any(c[0] == "dataframe" for c in calls)
    assert any(c[0] == "download_button" for c in calls)


def test_render_content_chart(sa_module):
    sa, calls, st = sa_module
    st.checkbox = lambda *a, **k: True
    calls.clear()
    sa.render_content({"type": "text", "text": "[{\"a\":1}]"}, 1)
    assert any(c[0] in {"line_chart", "bar_chart"} for c in calls)
