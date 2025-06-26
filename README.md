# MCP-PDI Sales Analytics Server

A Model Context Protocol (MCP) server providing real-time sales analytics tools for PDI Enterprise data.

## Features

- **Real-time Sales Data**: Query transaction-level data from V_LLM_SalesFact
- **Market Basket Analysis**: Discover item associations and purchase patterns
- **Sales Analytics**: Daily reports, trends, summaries, and performance metrics
- **MCP Compliant**: Works with any MCP-compatible client

## MCP tools

The API exposes each analytic function as its own tool. Tools may be accessed
via the `/mcp` SSE endpoint or directly by sending JSON to the corresponding
POST route.

### `sales_summary`

Aggregate KPIs between two dates. Use the `group_by` array to break down the
results by `date`, `hour`, `site`, `category`, or `department`. You can also
filter by a specific item using `item_id` or `item_name`.

### `sales_trend`

Return totals over time using an `interval` of `daily`, `weekly`, `monthly`, or
`hourly`. Optional `site_id` and `category` filters narrow the results.

### `hourly_sales`

Summarise quantities, sales totals and transaction counts for each hour between
`start_date` and `end_date`. Accepts an optional `site_id` filter.

### `daily_report`

Generate a simple per-day report of sales and transaction totals between
`start_date` and `end_date`. Optional filters include `site_id`, `item_id`,
`item_name` and `category`.

### `peak_hours`

Return the hours of the day with the highest sales totals between `start_date`
and `end_date`. Supports optional `site_id` filtering and limiting the number of
results via `top_n`.

### `sales_anomalies`

Highlight dates within `start_date` and `end_date` where total sales deviate
from the mean by more than `z_score` standard deviations. `site_id` is optional.

### `product_velocity`

List the fastest selling items between `start_date` and `end_date` ranked by
quantity. Optional `site_id` filtering and a `limit` parameter control the
number of results.

### `low_movement`

Identify items selling below a `threshold` between `start_date` and `end_date`.
Optionally filter by `site_id`.

### `sales_forecast`

Forecast daily sales for `horizon` days beyond the selected range using a Prophet model. Provide `start_date` and `end_date` for the training data.

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
`pyodbc` driver ("ODBC Driver 18 for SQL Server" by default). Additional options like `POOL_SIZE` and `MAX_OVERFLOW`
control connection pooling. See the example file for the full list of
supported variables.


## Running the FastAPI server

Install the dependencies and start the HTTP API with `uvicorn`:

```bash
pip install -r requirements.txt
uvicorn src.fastapi_server:create_app --host 0.0.0.0 --port 8000 --reload
```

Set `MCP_API_URL` if the API is not running on the default `http://localhost:8000`.

Each tool is exposed as its own endpoint (e.g. `POST /sales_summary`). The server
also mounts a streaming SSE interface at `/mcp` using **fastapi-mcp**.
All endpoints reject unknown parameters and will return a `422` error if extra
fields are supplied.
Launch it with:

```bash
python mcp_server.py
```


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

The frontend also includes options for viewing charts and exporting data:

- **Graphing** – Result tables can be displayed as bar or line graphs.
  Use the graph toggle to switch between tabular and visual views.
- **CSV Export** – Each table includes a **Download CSV** button
  for saving the query results for further analysis.


## Smoke testing

To verify the MCP server can be created without starting the HTTP API run:

```bash
python scripts/smoke_test_server.py
```
