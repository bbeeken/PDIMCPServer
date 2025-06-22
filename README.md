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

The server exposes two endpoints:
* `GET /tools` - list available tools
* `POST /call` - execute a tool by name

## Streamlit frontend

Run a lightweight UI to interact with the API:

```bash
streamlit run streamlit_app.py
```

Set `MCP_API_URL` if the API is not running on the default `http://localhost:8000`.

### Chat interface

Launch an experimental ChatGPT-style UI backed by a local Ollama model:

```bash
streamlit run streamlit_chat.py
```

Set `OLLAMA_MODEL` to choose the model name and `OLLAMA_HOST` if the Ollama server
is not running on `http://localhost:11434`.

## Smoke testing

To verify the MCP server can be created without starting the HTTP API run:

```bash
python scripts/smoke_test_server.py
```

