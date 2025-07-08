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


### `basket_metrics`

Compute overall basket-level metrics like transaction counts, total quantity, total sales, and the average number of items per transaction between `start_date` and `end_date`. Optionally filter by `site_id`.



### `cross_sell_opportunities`

Identify the items most often bought alongside a given product. Example parameters: `item_id=100`, `start_date="2024-01-01"`, `end_date="2024-01-31"`, `site_id=1`, `top_n=5`.

### `item_correlation`

Analyse baskets containing a target item to surface other products that frequently appear with it. Example parameters: `item_id=100`, `start_date="2024-01-01"`, `end_date="2024-01-31"`, `min_frequency=5`, `top_n=20`.

### `transaction_lookup`

Return the line items, quantities and totals for a specific `transaction_id`. An optional `site_id` parameter restricts results to a specific location.
 
 

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
These values are used to construct the SQLAlchemy `DATABASE_URL` automatically
with the `pyodbc` driver ("ODBC Driver 18 for SQL Server" by default). Additional options like `POOL_SIZE` and `MAX_OVERFLOW`
control connection pooling. See the example file for the full list of
supported variables.

The application automatically loads variables from this `.env` file
using **python-dotenv** when the database engine module is imported, so
no additional configuration is required.


## Running the FastAPI server

Install the dependencies and start the HTTP API with `uvicorn`:

```bash
pip install -r requirements.txt
uvicorn src.fastapi_server:create_app --host 0.0.0.0 --port 8006 --reload
```

Set `MCP_API_URL` if the API is not running on the default `http://localhost:8006`.

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

## Docker

A `Dockerfile` and `docker-compose.yml` are provided for containerised
deployment. Build the image with:

```bash
docker build -t mcp-pdi-server .
```

Create a `.env` file (see `.env.example`) and run:

```bash
docker compose up
```

The API will be available on `http://localhost:8000` and the Streamlit
interface on `http://localhost:8501`.

## Running tests

Install the dependencies, including the `mcp` and `httpx` packages, and run the
test suite with `pytest`:

```bash
pip install -r requirements.txt
pip install mcp httpx
pytest
```

Running `./setup.sh` will also install all required packages.

## Code style

This project uses [black](https://black.readthedocs.io/) for Python formatting. Run `scripts/check_format.sh` before committing or `black .` to format the code. CI also runs `black --check` to ensure consistency.


## Smoke testing

To verify the MCP server can be created without starting the HTTP API run:

```bash
python scripts/smoke_test_server.py
```

## License

This project is licensed under the [MIT License](LICENSE).

