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
settings. The variables `DB_SERVER`, `DB_DATABASE`, `DB_USERNAME`,
`DB_PASSWORD` and `DB_DRIVER` configure the SQL Server connection used by the
application. Additional options like `POOL_SIZE` and `MAX_OVERFLOW` control
connection pooling. See the example file for the full list of supported
variables.


## Running the FastAPI Server

Install the dependencies and launch the HTTP server with `uvicorn`:

```bash
pip install -r requirements.txt
uvicorn src.fastapi_server:create_app --host 0.0.0.0 --port 8000
```

The server exposes two endpoints:
* `GET /tools` - list available tools
* `POST /call` - execute a tool by name

## Running the FastAPI server

Start the HTTP API using `uvicorn`:

```bash
uvicorn src.fastapi_server:app --reload
```

This exposes `/tools` for listing tools and `/call` to execute them.

