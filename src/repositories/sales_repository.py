"""
Sales data repository with flexible query methods
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session
from ..db.models import SalesFact, Product, Organization
from .base import BaseRepository


class SalesRepository(BaseRepository[SalesFact]):
    """Repository for sales data queries"""

    def __init__(self, session: Session):
        super().__init__(SalesFact, session)

    def query_sales(
        self,
        start_date: date,
        end_date: date,
        item_name: Optional[str] = None,
        item_id: Optional[int] = None,
        site_id: Optional[int] = None,
        site_ids: Optional[List[int]] = None,
        category: Optional[str] = None,
        min_amount: Optional[float] = None,
        limit: int = 1000,
    ) -> List[SalesFact]:
        """
        Flexible sales query with optional filters
        """
        query = self.query()

        # Date range (required)
        query = self.filter_date_range(query, start_date, end_date)

        # Optional filters
        if item_id:
            query = query.filter(SalesFact.ItemID == item_id)
        elif item_name:
            # Smart item name search
            query = query.filter(SalesFact.ItemName.ilike(f"%{item_name}%"))

        # Site filtering - handles single or multiple sites
        if site_id:
            query = query.filter(SalesFact.SiteID == site_id)
        elif site_ids:
            query = query.filter(SalesFact.SiteID.in_(site_ids))

        if category:
            query = query.filter(SalesFact.Category.ilike(f"%{category}%"))

        if min_amount:
            query = query.filter(SalesFact.GrossSales >= min_amount)

        # Order by most recent first
        query = query.order_by(desc(SalesFact.SaleDate), desc(SalesFact.TimeOfDay))

        return query.limit(limit).all()

    def sales_summary(
        self,
        start_date: date,
        end_date: date,
        group_by: Optional[List[str]] = None,
        site_id: Optional[int] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Flexible sales summary with dynamic grouping
        """
        # Base aggregations
        aggregations = [
            func.count(func.distinct(SalesFact.TransactionID)).label(
                "transaction_count"
            ),
            func.count(func.distinct(SalesFact.ItemID)).label("unique_items"),
            func.sum(SalesFact.QtySold).label("total_quantity"),
            func.sum(SalesFact.GrossSales).label("total_sales"),
            func.avg(SalesFact.GrossSales).label("avg_sale_amount"),
        ]

        # Dynamic grouping
        group_columns = []
        select_columns = aggregations.copy()

        if group_by:
            for group in group_by:
                if group == "date":
                    group_columns.append(SalesFact.SaleDate)
                    select_columns.insert(0, SalesFact.SaleDate)
                elif group == "site":
                    group_columns.extend([SalesFact.SiteID, SalesFact.SiteName])
                    select_columns.insert(0, SalesFact.SiteID)
                    select_columns.insert(1, SalesFact.SiteName)
                elif group == "category":
                    group_columns.append(SalesFact.Category)
                    select_columns.insert(0, SalesFact.Category)
                elif group == "dayofweek":
                    group_columns.append(SalesFact.DayOfWeek)
                    select_columns.insert(0, SalesFact.DayOfWeek)

        # Build query
        query = self.session.query(*select_columns)
        query = self.filter_date_range(query, start_date, end_date)

        # Optional filters
        if site_id:
            query = query.filter(SalesFact.SiteID == site_id)
        if category:
            query = query.filter(SalesFact.Category.ilike(f"%{category}%"))

        # Apply grouping
        if group_columns:
            query = query.group_by(*group_columns)
            query = query.order_by(group_columns[0])

        # Execute and format results
        results = []
        for row in query.all():
            result_dict = {}
            for i, col in enumerate(query.column_descriptions):
                result_dict[col["name"]] = row[i]
            results.append(result_dict)

        return results

    def top_items(
        self,
        start_date: date,
        end_date: date,
        metric: str = "sales",
        top_n: int = 10,
        site_id: Optional[int] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get top selling items by various metrics
        """
        # Metric mapping
        metric_map = {
            "sales": func.sum(SalesFact.GrossSales),
            "quantity": func.sum(SalesFact.QtySold),
            "transactions": func.count(func.distinct(SalesFact.TransactionID)),
        }

        metric_column = metric_map.get(metric, metric_map["sales"]).label(
            "metric_value"
        )

        # Build query
        query = self.session.query(
            SalesFact.ItemID,
            SalesFact.ItemName,
            SalesFact.Category,
            SalesFact.Department,
            metric_column,
            func.count(func.distinct(SalesFact.SiteID)).label("site_count"),
            func.sum(SalesFact.QtySold).label("total_quantity"),
            func.sum(SalesFact.GrossSales).label("total_sales"),
        )

        query = self.filter_date_range(query, start_date, end_date)

        # Optional filters
        if site_id:
            query = query.filter(SalesFact.SiteID == site_id)
        if category:
            query = query.filter(SalesFact.Category.ilike(f"%{category}%"))

        # Group and order
        query = query.group_by(
            SalesFact.ItemID,
            SalesFact.ItemName,
            SalesFact.Category,
            SalesFact.Department,
        )
        query = query.order_by(desc("metric_value"))
        query = query.limit(top_n)

        # Format results
        results = []
        for i, row in enumerate(query.all()):
            results.append(
                {
                    "rank": i + 1,
                    "item_id": row.ItemID,
                    "item_name": row.ItemName,
                    "category": row.Category,
                    "department": row.Department,
                    "metric_value": float(row.metric_value),
                    "site_count": row.site_count,
                    "total_quantity": float(row.total_quantity),
                    "total_sales": float(row.total_sales),
                }
            )

        return results
