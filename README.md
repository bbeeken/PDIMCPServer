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


## Running the FastAPI server

Install the dependencies and start the HTTP API with `uvicorn`:

```bash
pip install -r requirements.txt
uvicorn src.fastapi_server:create_app --host 0.0.0.0 --port 8000 --reload
```

The server exposes two endpoints:
* `GET /tools` - list available tools
* `POST /call` - execute a tool by name

