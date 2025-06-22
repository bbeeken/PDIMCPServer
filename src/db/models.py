"""
SQLAlchemy ORM models for PDI views
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Time, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func

Base = declarative_base()


# Fully qualified database view names

# Fully qualified view name for SalesFact

SALES_FACT_VIEW = "dbo.V_LLM_SalesFact"

class SalesFact(Base):
    """V_LLM_SalesFact - Real-time sales transactions"""
    __tablename__ = 'V_LLM_SalesFact'
    __table_args__ = {'schema': 'dbo'}
    
    # Composite primary key for views
    TransactionID = Column(Integer, primary_key=True)
    LineItemNumber = Column(Integer, primary_key=True)
    
    # Date and time
    SaleDate = Column(Date, nullable=False, index=True)
    DayOfWeek = Column(String(20))
    TimeOfDay = Column(Time)
    
    # Location
    SiteID = Column(Integer, nullable=False, index=True)
    SiteName = Column(String(100))
    
    # Product
    ProductKey = Column(Integer)
    ItemID = Column(Integer, nullable=False, index=True)
    ItemName = Column(String(255))
    Category = Column(String(100), index=True)
    Department = Column(String(100))
    
    # Metrics
    QtySold = Column(Float, default=0)
    Price = Column(Float, default=0)
    GrossSales = Column(Float, default=0)
    
    def __repr__(self):
        return f"<Sale {self.TransactionID}-{self.LineItemNumber}: {self.ItemName} ${self.GrossSales}>"

class Product(Base):
    """Product master data"""
    __tablename__ = 'Product'
    __table_args__ = {'schema': 'dbo'}
    
    Product_Key = Column(Integer, primary_key=True)
    Item_ID = Column(Integer, unique=True, nullable=False)
    Item_Desc = Column(String(255))
    Category_ID = Column(String(50))
    Category_Desc = Column(String(100))
    Department_ID = Column(String(50))
    Department_Desc = Column(String(100))
    UPC = Column(String(50))
    Size_Desc = Column(String(50))
    
    def __repr__(self):
        return f"<Product {self.Item_ID}: {self.Item_Desc}>"

class Organization(Base):
    """Store/Site information"""
    __tablename__ = 'Organization'
    __table_args__ = {'schema': 'dbo'}
    
    organization_key = Column(Integer, primary_key=True)
    Location_ID = Column(Integer, unique=True)
    Location_Desc = Column(String(100))
    Site_id = Column(Integer)
    GPS_City = Column(String(100))
    GPS_State = Column(String(2))
    GPS_Latitude = Column(Float)
    GPS_Longitude = Column(Float)
    
    def __repr__(self):
        return f"<Site {self.Site_id}: {self.Location_Desc}>"