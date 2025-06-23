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

    def record_return(name, value):
        def fn(*args, **kwargs):
            calls.append((name, args, kwargs))
            return value
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
    st.bar_chart = record("bar_chart")
    st.radio = record_return("radio", "Line")
    st.error = record("error")
    def chat_message(role):
        class Ctx:
            def __enter__(self_inner):
                calls.append(("chat_message", role))
                return self_inner
            def __exit__(self_inner, exc_type, exc, tb):
                pass
        return Ctx()

    st.chat_message = chat_message
    st.chat_input = lambda *a, **kw: None
    st.empty = record("empty")

    pd = types.ModuleType("pandas")
    class DF:
        def __init__(self):
            self.columns = ["num"]

        def select_dtypes(self, *a, **k):
            return self

        def __getitem__(self, key):
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


def test_render_message_json_csv(chat_module, monkeypatch):
    chat, calls = chat_module
    msgs = [
        "```json\n[{\"a\":1}]\n```",
        "```csv\na,b\n1,2\n```",
    ]
    for msg in msgs:
        calls.clear()
        chat.render_message(msg)
        assert any(c[0] == "dataframe" for c in calls)
        assert any(c[0] == "line_chart" for c in calls)
        assert any(c[0] == "radio" for c in calls)

    def radio_bar(*args, **kwargs):
        calls.append(("radio", args, kwargs))
        return "Bar"

    monkeypatch.setattr(chat.st, "radio", radio_bar)
    for msg in msgs:
        calls.clear()
        chat.render_message(msg)
        assert any(c[0] == "bar_chart" for c in calls)


def test_chat_env_options(monkeypatch):
    monkeypatch.setenv("OLLAMA_TEMPERATURE", "0.5")
    monkeypatch.setenv("OLLAMA_TOP_P", "0.75")
    monkeypatch.setenv("OLLAMA_TOP_K", "32")

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
    st.bar_chart = record("bar_chart")
    st.radio = lambda *a, **kw: (calls.append(("radio", a, kw)) or "Line")
    st.error = record("error")
    def chat_message(role):
        class Ctx:
            def __enter__(self_inner):
                calls.append(("chat_message", role))
                return self_inner
            def __exit__(self_inner, exc_type, exc, tb):
                pass
        return Ctx()

    st.chat_message = chat_message
    st.chat_input = lambda *a, **kw: "hi"
    st.empty = record("empty")

    pd = types.ModuleType("pandas")

    class DF:
        def __init__(self):
            self.columns = ["num"]

        def select_dtypes(self, *a, **k):
            return self

        def __getitem__(self, key):
            return self

    pd.DataFrame = lambda data: calls.append(("DataFrame", data)) or DF()
    pd.read_csv = lambda buf: calls.append(("read_csv", buf.getvalue())) or DF()

    ollama_mod = types.ModuleType("ollama")

    def fake_chat(**kwargs):
        calls.append(("ollama.chat", kwargs))
        yield {"message": {"content": "ok"}}

    ollama_mod.chat = fake_chat

    monkeypatch.setitem(sys.modules, "streamlit", st)
    monkeypatch.setitem(sys.modules, "pandas", pd)
    monkeypatch.setitem(sys.modules, "ollama", ollama_mod)

    importlib.reload(importlib.import_module("pages.chat"))

    assert any(c[0] == "ollama.chat" and c[1]["options"] == {"temperature": 0.5, "top_p": 0.75, "top_k": 32} for c in calls)

