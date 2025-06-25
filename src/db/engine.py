"""
SQLAlchemy engine configuration
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

# Build connection URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Build from components
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")

    # Use the pyodbc driver with an explicit ODBC driver name
    driver = os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
    driver_param = driver.replace(" ", "+")
    DATABASE_URL = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver_param}"
    )

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=int(os.getenv("POOL_SIZE", "10")),
    max_overflow=int(os.getenv("MAX_OVERFLOW", "20")),
    pool_pre_ping=True,  # Verify connections before using
    poolclass=QueuePool,
    echo=False,  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
