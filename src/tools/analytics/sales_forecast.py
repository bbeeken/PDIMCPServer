"""Generate a sales forecast using Prophet."""

from typing import Dict, Any

import pandas as pd
from prophet import Prophet
from mcp.types import Tool

from ...db.connection import execute_query
from ...db.models import SALES_FACT_VIEW
from ..utils import validate_date_range, create_tool_response


async def sales_forecast_impl(
    start_date: str,
    end_date: str,
    horizon: int = 7,
) -> Dict[str, Any]:
    """Return a forecast of daily sales totals."""

    start_date, end_date = validate_date_range(start_date, end_date)

    sql = f"""
    SELECT SaleDate AS ds, SUM(GrossSales) AS y
    FROM {SALES_FACT_VIEW}
    WHERE SaleDate BETWEEN :start_date AND :end_date
    GROUP BY SaleDate
    ORDER BY SaleDate
    """

    params = {"start_date": start_date, "end_date": end_date}

    try:
        rows = execute_query(sql, params)
        df = pd.DataFrame(rows)
        if df.empty:
            return create_tool_response([], sql, params, error="No data found")
        df["ds"] = pd.to_datetime(df["ds"])
        model = Prophet()
        model.fit(df)
        future = model.make_future_dataframe(periods=horizon)
        forecast = model.predict(future)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        forecast["ds"] = forecast["ds"].dt.strftime("%Y-%m-%d")
        data = forecast.to_dict(orient="records")
        meta = {"date_range": f"{start_date} to {end_date}", "horizon": horizon}
        return create_tool_response(data, sql, params, meta)
    except Exception as exc:  # noqa: BLE001
        return create_tool_response([], sql, params, error=str(exc))


sales_forecast_tool = Tool(
    name="sales_forecast",
    description="Forecast daily sales totals using Prophet.",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "format": "date"},
            "end_date": {"type": "string", "format": "date"},
            "horizon": {
                "type": "integer",
                "default": 7,
                "description": "Days to forecast beyond end_date",
            },
        },
        "required": ["start_date", "end_date"],
        "additionalProperties": False,
    },
)

sales_forecast_tool._implementation = sales_forecast_impl
