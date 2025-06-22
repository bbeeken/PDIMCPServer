"""
Base repository with common query patterns
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from datetime import date, datetime
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_, or_, func
from ..db.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common database operations"""

    def __init__(self, model: Type[ModelType], session: Session):
        self.model = model
        self.session = session

    def query(self) -> Query:
        """Get base query for the model"""
        return self.session.query(self.model)

    def filter_date_range(
        self,
        query: Query,
        start_date: date,
        end_date: date,
        date_field: str = "SaleDate",
    ) -> Query:
        """Apply date range filter"""
        date_column = getattr(self.model, date_field)
        return query.filter(and_(date_column >= start_date, date_column <= end_date))

    def filter_optional(self, query: Query, **kwargs) -> Query:
        """Apply optional filters dynamically"""
        for field, value in kwargs.items():
            if value is not None:
                column = getattr(self.model, field, None)
                if column is not None:
                    if isinstance(value, str) and "%" in value:
                        # LIKE query
                        query = query.filter(column.like(value))
                    elif isinstance(value, list):
                        # IN query
                        query = query.filter(column.in_(value))
                    else:
                        # Exact match
                        query = query.filter(column == value)
        return query

    def paginate(self, query: Query, limit: int = 1000, offset: int = 0) -> Query:
        """Apply pagination"""
        return query.limit(limit).offset(offset)
