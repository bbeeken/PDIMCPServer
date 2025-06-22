import os
import json
import httpx
import pandas as pd
import streamlit as st
import ollama

SERVER_URL = os.getenv("MCP_API_URL", "http://localhost:8000")
MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

@st.cache_data
def load_tools():
    resp = httpx.get(f"{SERVER_URL}/tools")
    resp.raise_for_status()
    return resp.json()

def display_outputs(outputs):
    """Render tool outputs with optional charts."""
    for content in outputs:
        if content.get("type") != "text":
            st.json(content)
            continue
        text = content.get("text", "")
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            st.text(text)
            continue

        if isinstance(obj, dict) and "data" in obj:
            st.json(obj)
            df = pd.DataFrame(obj["data"])
            if not df.empty:
                st.dataframe(df)
                numeric_cols = df.select_dtypes(include="number")
                if not numeric_cols.empty:
                    st.line_chart(numeric_cols)
        else:
            st.text(text)

def tools_ui(tools):
    """Form-based interface for calling server tools."""
    tool_names = [t.get("name", "") for t in tools]
    selected_name = st.sidebar.selectbox("Select Tool", tool_names)
    current_tool = next((t for t in tools if t.get("name") == selected_name), {})

    st.header(selected_name)
    st.write(current_tool.get("description", ""))

    input_schema = current_tool.get("inputSchema", {})
    properties = input_schema.get("properties", {})
    required = set(input_schema.get("required", []))

    args = {}
    with st.form("tool_form"):
        for field, schema in properties.items():
            field_type = schema.get("type", "string")
            label = f"{field} ({field_type})"
            default = schema.get("default")
            if field_type in ("number", "integer"):
                value = st.number_input(label, value=default or 0)
            elif field_type == "boolean":
                value = st.checkbox(label, value=bool(default))
            else:
                value = st.text_input(label, value=default or "")
            if value != "" or field in required:
                args[field] = value
        submitted = st.form_submit_button("Run")

    if submitted:
        with st.spinner("Calling tool..."):
            try:
                resp = httpx.post(
                    f"{SERVER_URL}/call",
                    json={"name": selected_name, "arguments": args},
                )
                resp.raise_for_status()
                display_outputs(resp.json())
            except Exception as exc:  # pragma: no cover - external service
                st.error(f"Error calling tool: {exc}")

def chat_ui():
    """ChatGPT-style interface backed by Ollama."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

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

def main() -> None:
    st.set_page_config(page_title="MCP Tools & Chat", page_icon="\U0001F4AC")
    st.title("MCP PDI Interface")
    mode = st.sidebar.radio("Mode", ("Tools", "Chat"))

    if mode == "Chat":
        chat_ui()
        return

    try:
        tools = load_tools()
    except Exception as exc:  # pragma: no cover - external service
        st.error(f"Failed to fetch tools: {exc}")
        return

    tools_ui(tools)

if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
