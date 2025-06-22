"""
Market basket analysis repository
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import date
from sqlalchemy import func, and_, or_, desc, Float
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import text
from ..db.models import SalesFact
from .base import BaseRepository

class BasketRepository(BaseRepository[SalesFact]):
    """Repository for market basket analysis"""
    
    def __init__(self, session: Session):
        super().__init__(SalesFact, session)
    
    def basket_analysis(
        self,
        start_date: date,
        end_date: date,
        min_support: float = 0.01,
        min_confidence: float = 0.5,
        site_id: Optional[int] = None,
        max_items: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find frequently bought together items with lift analysis
        """
        # Create aliases for self-join
        item1 = aliased(SalesFact)
        item2 = aliased(SalesFact)
        
        # Base filters
        base_filters = [
            item1.SaleDate >= start_date,
            item1.SaleDate <= end_date
        ]
        if site_id:
            base_filters.append(item1.SiteID == site_id)
        
        # Count total transactions
        total_transactions = self.session.query(
            func.count(func.distinct(SalesFact.TransactionID))
        ).filter(and_(*base_filters)).scalar()
        
        if total_transactions == 0:
            return []
        
        # Find item pairs
        pairs_query = self.session.query(
            item1.ItemID.label('item1_id'),
            item1.ItemName.label('item1_name'),
            item2.ItemID.label('item2_id'),
            item2.ItemName.label('item2_name'),
            func.count(func.distinct(item1.TransactionID)).label('pair_count')
        ).select_from(item1).join(
            item2,
            and_(
                item1.TransactionID == item2.TransactionID,
                item1.ItemID < item2.ItemID  # Avoid duplicates
            )
        ).filter(
            and_(*base_filters)
        ).group_by(
            item1.ItemID,
            item1.ItemName,
            item2.ItemID,
            item2.ItemName
        )
        
        # Calculate support
        min_count = int(total_transactions * min_support)
        pairs_query = pairs_query.having(
            func.count(func.distinct(item1.TransactionID)) >= min_count
        )
        
        # Execute and calculate metrics
        results = []
        for pair in pairs_query.all():
            # Get individual item frequencies
            item1_count = self._get_item_frequency(
                pair.item1_id, start_date, end_date, site_id
            )
            item2_count = self._get_item_frequency(
                pair.item2_id, start_date, end_date, site_id
            )
            
            # Calculate metrics
            support = pair.pair_count / total_transactions
            confidence = pair.pair_count / item1_count if item1_count > 0 else 0
            lift = (pair.pair_count * total_transactions) / (item1_count * item2_count) if item1_count > 0 and item2_count > 0 else 0
            
            if confidence >= min_confidence:
                results.append({
                    'item1': {'id': pair.item1_id, 'name': pair.item1_name},
                    'item2': {'id': pair.item2_id, 'name': pair.item2_name},
                    'support': round(support, 4),
                    'confidence': round(confidence, 3),
                    'lift': round(lift, 2),
                    'frequency': pair.pair_count
                })
        
        # Sort by lift descending
        results.sort(key=lambda x: x['lift'], reverse=True)
        return results[:max_items]
    
    def item_correlation(
        self,
        item_id: int,
        start_date: date,
        end_date: date,
        min_frequency: int = 5,
        top_n: int = 20,
        site_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Find items frequently bought with a specific item
        """
        # Get target item info
        target_item = self.session.query(
            SalesFact.ItemName,
            SalesFact.Category
        ).filter(
            SalesFact.ItemID == item_id
        ).first()
        
        if not target_item:
            return {'target_item': {'id': item_id}, 'correlations': []}
        
        # Find transactions with target item
        target_transactions = self.session.query(
            SalesFact.TransactionID
        ).filter(
            and_(
                SalesFact.ItemID == item_id,
                SalesFact.SaleDate >= start_date,
                SalesFact.SaleDate <= end_date
            )
        )
        
        if site_id:
            target_transactions = target_transactions.filter(SalesFact.SiteID == site_id)
        
        target_transaction_ids = [t[0] for t in target_transactions.all()]
        target_count = len(target_transaction_ids)
        
        if target_count == 0:
            return {
                'target_item': {
                    'id': item_id,
                    'name': target_item.ItemName,
                    'category': target_item.Category
                },
                'correlations': []
            }
        
        # Find correlated items
        correlated = self.session.query(
            SalesFact.ItemID,
            SalesFact.ItemName,
            SalesFact.Category,
            func.count(func.distinct(SalesFact.TransactionID)).label('co_occurrence'),
            func.avg(SalesFact.QtySold).label('avg_qty'),
            func.avg(SalesFact.GrossSales).label('avg_sales')
        ).filter(
            and_(
                SalesFact.TransactionID.in_(target_transaction_ids),
                SalesFact.ItemID != item_id,
                SalesFact.SaleDate >= start_date,
                SalesFact.SaleDate <= end_date
            )
        )
        
        if site_id:
            correlated = correlated.filter(SalesFact.SiteID == site_id)
        
        correlated = correlated.group_by(
            SalesFact.ItemID,
            SalesFact.ItemName,
            SalesFact.Category
        ).having(
            func.count(func.distinct(SalesFact.TransactionID)) >= min_frequency
        ).order_by(
            desc('co_occurrence')
        ).limit(top_n)
        
        # Calculate metrics
        correlations = []
        for item in correlated.all():
            confidence = item.co_occurrence / target_count
            
            correlations.append({
                'item': {
                    'id': item.ItemID,
                    'name': item.ItemName,
                    'category': item.Category
                },
                'metrics': {
                    'co_occurrence_count': item.co_occurrence,
                    'confidence': round(confidence, 3)
                },
                'purchase_behavior': {
                    'avg_qty_together': round(float(item.avg_qty), 2),
                    'avg_sales_together': round(float(item.avg_sales), 2)
                }
            })
        
        return {
            'target_item': {
                'id': item_id,
                'name': target_item.ItemName,
                'category': target_item.Category
            },
            'correlations': correlations
        }
    
    def basket_metrics(
        self,
        start_date: date,
        end_date: date,
        group_by: Optional[List[str]] = None,
        site_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate basket-level metrics
        """
        # Subquery for basket data
        basket_subquery = self.session.query(
            SalesFact.TransactionID,
            func.count(func.distinct(SalesFact.ItemID)).label('unique_items'),
            func.sum(SalesFact.QtySold).label('total_quantity'),
            func.sum(SalesFact.GrossSales).label('basket_value')
        )
        
        # Add grouping columns to subquery
        group_columns = []
        if group_by:
            for group in group_by:
                if group == 'site':
                    basket_subquery = basket_subquery.add_columns(
                        SalesFact.SiteID,
                        SalesFact.SiteName
                    )
                    group_columns.extend(['SiteID', 'SiteName'])
                elif group == 'dayofweek':
                    basket_subquery = basket_subquery.add_columns(SalesFact.DayOfWeek)
                    group_columns.append('DayOfWeek')
                elif group == 'date':
                    basket_subquery = basket_subquery.add_columns(SalesFact.SaleDate)
                    group_columns.append('SaleDate')
        
        # Apply filters
        basket_subquery = basket_subquery.filter(
            and_(
                SalesFact.SaleDate >= start_date,
                SalesFact.SaleDate <= end_date
            )
        )
        
        if site_id:
            basket_subquery = basket_subquery.filter(SalesFact.SiteID == site_id)
        
        # Group by transaction and any additional columns
        group_by_columns = [SalesFact.TransactionID]
        if group_columns:
            for col in group_columns:
                group_by_columns.append(getattr(SalesFact, col))
        
        basket_subquery = basket_subquery.group_by(*group_by_columns)
        basket_data = basket_subquery.subquery()
        
        # Main query for metrics
        metrics_query = self.session.query(
            func.count(basket_data.c.TransactionID).label('transaction_count'),
            func.avg(basket_data.c.unique_items).label('avg_unique_items'),
            func.avg(basket_data.c.total_quantity).label('avg_quantity'),
            func.avg(basket_data.c.basket_value).label('avg_basket_value'),
            func.min(basket_data.c.basket_value).label('min_basket_value'),
            func.max(basket_data.c.basket_value).label('max_basket_value'),
            func.stddev(basket_data.c.basket_value).label('std_basket_value')
        )
        
        # Add grouping columns to final query
        if group_columns:
            for col in group_columns:
                metrics_query = metrics_query.add_columns(basket_data.c[col])
            metrics_query = metrics_query.group_by(*[basket_data.c[col] for col in group_columns])
        
        # Execute and format
        results = []
        for row in metrics_query.all():
            result = {
                'transaction_count': row.transaction_count,
                'avg_unique_items': round(float(row.avg_unique_items or 0), 2),
                'avg_quantity': round(float(row.avg_quantity or 0), 2),
                'avg_basket_value': round(float(row.avg_basket_value or 0), 2),
                'min_basket_value': round(float(row.min_basket_value or 0), 2),
                'max_basket_value': round(float(row.max_basket_value or 0), 2),
                'std_basket_value': round(float(row.std_basket_value or 0), 2)
            }
            
            # Add grouping values
            for i, col in enumerate(group_columns):
                result[col] = row[7 + i]  # After the 7 metric columns
            
            results.append(result)
        
        return results
    
    def _get_item_frequency(self, item_id: int, start_date: date, 
                           end_date: date, site_id: Optional[int]) -> int:
        """Helper to get item transaction frequency"""
        query = self.session.query(
            func.count(func.distinct(SalesFact.TransactionID))
        ).filter(
            and_(
                SalesFact.ItemID == item_id,
                SalesFact.SaleDate >= start_date,
                SalesFact.SaleDate <= end_date
            )
        )
        
        if site_id:
            query = query.filter(SalesFact.SiteID == site_id)
        
        return query.scalar() or 0
