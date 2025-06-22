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
