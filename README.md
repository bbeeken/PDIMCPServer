# MCP-PDI Sales Analytics Server

A Model Context Protocol (MCP) server providing real-time sales analytics tools for PDI Enterprise data.

## Features

- **Real-time Sales Data**: Query transaction-level data from V_LLM_SalesFact
- **Market Basket Analysis**: Discover item associations and purchase patterns
- **Sales Analytics**: Trends, summaries, and performance metrics
- **MCP Compliant**: Works with any MCP-compatible client

## Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd mcp-pdi-server
```

## Database Setup

Create a `.env` file based on `.env.example` and adjust the connection
settings. The variables `DB_SERVER`, `DB_DATABASE`, `DB_USERNAME`, and
`DB_PASSWORD` configure the SQL Server connection used by the application.
`DATABASE_URL` combines these into a standard SQLAlchemy URL using the
`pymssql` driver. Additional options like `POOL_SIZE` and `MAX_OVERFLOW`
control connection pooling. See the example file for the full list of
supported variables.


## Running the FastAPI server

Install the dependencies and start the HTTP API with `uvicorn`:

```bash
pip install -r requirements.txt
uvicorn src.fastapi_server:create_app --host 0.0.0.0 --port 8000 --reload
```

Set `MCP_API_URL` if the API is not running on the default `http://localhost:8000`.

The server exposes two endpoints:
* `GET /tools` - list available tools
* `POST /call` - execute a tool by name

## Streamlit frontend

Launch the web interface with:

```bash
streamlit run streamlit_app.py
```


Set `MCP_API_URL` if the FastAPI server is not running on `http://localhost:8000`.
The **Chat** page uses a local Ollama model; configure `OLLAMA_MODEL` to select the
model and `OLLAMA_HOST` if the Ollama server is not at `http://localhost:11434`.
Chat generation can also be tuned with:
`OLLAMA_TEMPERATURE` (0-1), `OLLAMA_TOP_P`, and `OLLAMA_TOP_K`.

On the main page, select a tool from the sidebar and fill in the generated form
to call the API. Returned text or JSON/CSV output is displayed below the form.

The chat page can render tables and simple line charts when JSON or CSV is
included inside fenced code blocks.


## Smoke testing

To verify the MCP server can be created without starting the HTTP API run:

```bash
python scripts/smoke_test_server.py
```
