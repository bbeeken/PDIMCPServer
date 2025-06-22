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
