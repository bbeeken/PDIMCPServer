import os
import re
import json
from io import StringIO

import pandas as pd
import streamlit as st
import ollama

MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Lazily configure an Ollama client if the package provides the Client class.
# Tests replace the ``ollama`` module with a minimal stub that lacks this
# attribute, so guard against AttributeError during import.
client = ollama.Client(host=OLLAMA_HOST) if hasattr(ollama, "Client") else None

st.set_page_config(page_title="MCP Chat", page_icon="💬", layout="wide")

# Simple CSS to mimic ChatGPT-style bubbles
st.markdown(
    """
    <style>
    .user-msg,
    .assistant-msg {
        padding: 0.5rem 0.75rem;
        border-radius: 0.5rem;
        margin: 0.25rem 0;
        max-width: 60ch;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 1rem;
        line-height: 1.4;
    }
    .user-msg {
        background-color: #DCF8C6;
        border: 1px solid #cbe5b9;
        margin-left: auto;
    }
    .assistant-msg {
        background-color: #F7F7F8;
        border: 1px solid #e4e4e5;
        margin-right: auto;
    }
    .user-msg code,
    .assistant-msg code {
        font-family: "Courier New", monospace;
        font-size: 0.9rem;
    }
    div[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] {
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

st.title("MCP Chat (Ollama)")


def scroll_to_bottom() -> None:
    """Scroll the page to the bottom using JavaScript."""
    st.markdown(
        """
        <script>
        window.scrollTo(0, document.body.scrollHeight);
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_message(content: str) -> None:
    """Render a chat message supporting code blocks and charts."""
    pattern = re.compile(r"```(\w+)?[ \t]*\n?(.*?)```", re.DOTALL)
    pos = 0
    for match in pattern.finditer(content):
        st.markdown(content[pos : match.start()])
        lang = (match.group(1) or "").lower()
        data = match.group(2)
        if lang in {"json", "csv"}:
            try:
                if lang == "json":
                    df = pd.DataFrame(json.loads(data))
                else:
                    df = pd.read_csv(StringIO(data))
            except Exception:
                st.markdown(match.group(0))
            else:
                st.dataframe(df)
                num_cols = df.select_dtypes("number").columns
                if len(num_cols) > 0:
                    st.line_chart(df[num_cols])
        else:
            st.code(data, language=lang or None)
        pos = match.end()
    if pos < len(content):
        st.markdown(content[pos:])


for msg in st.session_state.messages:
    css = "user-msg" if msg["role"] == "user" else "assistant-msg"
    with st.chat_message(msg["role"]):
        st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
        render_message(msg["content"])
        st.markdown("</div>", unsafe_allow_html=True)
scroll_to_bottom()

prompt = st.chat_input("Ask something...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="user-msg">{prompt}</div>', unsafe_allow_html=True)
    scroll_to_bottom()
    with st.chat_message("assistant"):
        st.markdown('<div class="assistant-msg">', unsafe_allow_html=True)
        try:
            if client is not None:
                response_stream = client.chat(
                    model=MODEL,
                    messages=st.session_state.messages,
                    stream=True,
                )
            else:
                response_stream = ollama.chat(
                    model=MODEL,
                    messages=st.session_state.messages,
                    host=OLLAMA_HOST,
                    stream=True,
                )
            chunks = []
            placeholder = st.empty()
            for chunk in response_stream:
                part = chunk["message"]["content"]
                chunks.append(part)
                placeholder.markdown("".join(chunks))
                scroll_to_bottom()
            content = "".join(chunks)
        except Exception as exc:  # pragma: no cover - external service
            st.error(f"Error contacting Ollama: {exc}")
            content = ""
        if content:
            st.session_state.messages.append({"role": "assistant", "content": content})
            placeholder.empty()

            render_message(content)

            st.markdown('</div>', unsafe_allow_html=True)
            scroll_to_bottom()


