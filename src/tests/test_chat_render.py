import importlib
import sys
import types

import pytest


class SessionState(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


@pytest.fixture()
def chat_module(monkeypatch):
    calls = []
    st = types.ModuleType("streamlit")
    st.session_state = SessionState({"messages": []})

    def record(name):
        def fn(*args, **kwargs):
            calls.append((name, args, kwargs))
            return Placeholder() if name == "empty" else None
        return fn

    class Placeholder:
        def markdown(self, text, **kwargs):
            calls.append(("placeholder.markdown", text))
        def empty(self):
            calls.append(("placeholder.empty",))
        def container(self):
            return self

    st.set_page_config = record("set_page_config")
    st.markdown = record("markdown")
    st.title = record("title")
    st.code = record("code")
    st.dataframe = record("dataframe")
    st.line_chart = record("line_chart")
    st.error = record("error")
    st.chat_message = lambda role: types.SimpleNamespace(__enter__=lambda self: calls.append(("chat_message", role)) or self, __exit__=lambda self, exc_type, exc, tb: None)
    st.chat_input = lambda *a, **kw: None
    st.empty = record("empty")

    pd = types.ModuleType("pandas")
    class DF:
        def __init__(self):
            self.columns = []

        def select_dtypes(self, *a, **k):
            return self
    pd.DataFrame = lambda data: calls.append(("DataFrame", data)) or DF()
    pd.read_csv = lambda buf: calls.append(("read_csv", buf.getvalue())) or DF()

    monkeypatch.setitem(sys.modules, "streamlit", st)
    monkeypatch.setitem(sys.modules, "pandas", pd)
    monkeypatch.setitem(sys.modules, "ollama", types.ModuleType("ollama"))

    chat = importlib.reload(importlib.import_module("pages.chat"))
    calls.clear()
    return chat, calls


def test_render_message_code_variants(chat_module):
    chat, calls = chat_module
    msgs = [
        "pre\n```python\nprint(1)\n```\npost",
        "pre\n```python   \nprint(1)\n```\npost",
        "pre\n```python print(1)```\npost",
    ]
    for msg in msgs:
        calls.clear()
        chat.render_message(msg)
        assert any(c[0] == "code" for c in calls)


def test_render_message_json_csv(chat_module):
    chat, calls = chat_module
    msgs = [
        "```json\n[{\"a\":1}]\n```",
        "```csv\na,b\n1,2\n```",
    ]
    for msg in msgs:
        calls.clear()
        chat.render_message(msg)
        assert any(c[0] == "dataframe" for c in calls)

