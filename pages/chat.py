import os
import re
import json
from io import StringIO

import pandas as pd
import streamlit as st
import ollama

MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

st.set_page_config(page_title="MCP Chat", page_icon="💬")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

st.title("MCP Chat (Ollama)")


def render_message(content: str) -> None:
    """Render a chat message with optional charts."""
    pattern = re.compile(r"```(json|csv)\n(.*?)```", re.DOTALL | re.IGNORECASE)
    pos = 0
    for match in pattern.finditer(content):
        st.markdown(content[pos : match.start()])
        lang = match.group(1).lower()
        data = match.group(2)
        try:
            if lang == "json":
                df = pd.DataFrame(json.loads(data))
            else:  # csv
                df = pd.read_csv(StringIO(data))
        except Exception:
            st.markdown(match.group(0))
        else:
            st.dataframe(df)
            num_cols = df.select_dtypes("number").columns
            if len(num_cols) > 0:
                st.line_chart(df[num_cols])
        pos = match.end()
    if pos < len(content):
        st.markdown(content[pos:])


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        render_message(msg["content"])

prompt = st.chat_input("Ask something...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
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
            content = "".join(chunks)
        except Exception as exc:  # pragma: no cover - external service
            st.error(f"Error contacting Ollama: {exc}")
            content = ""
        if content:
            st.session_state.messages.append({"role": "assistant", "content": content})
            placeholder.empty()
            render_message(content)
