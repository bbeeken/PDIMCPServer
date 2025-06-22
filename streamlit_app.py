
import json
from typing import Any, Dict, List

import pandas as pd
import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.title("PDI Sales Analytics")


def fetch_tools() -> List[str]:
    """Retrieve list of tool names from the API."""
    resp = requests.get(f"{API_URL}/tools")
    resp.raise_for_status()
    return [t["name"] for t in resp.json()]


def call_tool(name: str, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Call a tool and return its response."""
    resp = requests.post(f"{API_URL}/call", json={"name": name, "arguments": args})
    resp.raise_for_status()
    return resp.json()


tool_names = fetch_tools()
selected_tool = st.selectbox("Tool", tool_names)
args_text = st.text_area("Arguments (JSON)", "{}")

if st.button("Run"):
    try:
        args = json.loads(args_text) if args_text.strip() else {}
    except json.JSONDecodeError:
        st.error("Invalid JSON arguments")
        st.stop()

    contents = call_tool(selected_tool, args)

    for content in contents:
        text = content.get("text", "")
        try:
            data = json.loads(text)
            df = pd.DataFrame(data)
        except Exception:
            df = None

        if isinstance(df, pd.DataFrame) and not df.empty:
            st.dataframe(df)

            numeric_cols = df.select_dtypes(include="number").columns
            if len(numeric_cols) > 0:
                st.line_chart(df[numeric_cols])

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "results.csv", "text/csv")
        else:
            st.text(text)

import os
import httpx
import streamlit as st

SERVER_URL = os.getenv("MCP_API_URL", "http://localhost:8000")

@st.cache_data
def load_tools():
    resp = httpx.get(f"{SERVER_URL}/tools")
    resp.raise_for_status()
    return resp.json()

def main() -> None:
    st.title("MCP PDI Sales Tools")
    try:
        tools = load_tools()
    except Exception as exc:  # pragma: no cover - external service
        st.error(f"Failed to fetch tools: {exc}")
        return

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
                resp = httpx.post(f"{SERVER_URL}/call", json={"name": selected_name, "arguments": args})
                resp.raise_for_status()
                outputs = resp.json()
                for content in outputs:
                    if content.get("type") == "text":
                        st.text(content.get("text", ""))
                    else:
                        st.json(content)
            except Exception as exc:  # pragma: no cover - external service
                st.error(f"Error calling tool: {exc}")

if __name__ == "__main__":  # pragma: no cover - manual execution
    main()

