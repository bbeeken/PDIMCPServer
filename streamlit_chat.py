import os
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

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

prompt = st.chat_input("Ask something...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        try:
            response = ollama.chat(
                model=MODEL,
                messages=st.session_state.messages,
                host=OLLAMA_HOST,
            )
            content = response["message"]["content"]
        except Exception as exc:  # pragma: no cover - external service
            st.error(f"Error contacting Ollama: {exc}")
            content = ""
        if content:
            st.session_state.messages.append({"role": "assistant", "content": content})
            st.write(content)
