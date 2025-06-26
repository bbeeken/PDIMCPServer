"""Database engine configuration."""

import os
import logging
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# Get environment variables
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DATABASE_URL_ENV = os.getenv("DATABASE_URL")
ODBC_DRIVER = os.getenv("ODBC_DRIVER", "ODBC Driver 17 for SQL Server")
POOL_SIZE = int(os.getenv("POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("MAX_OVERFLOW", "20"))

if DATABASE_URL_ENV:
    DATABASE_URL = DATABASE_URL_ENV
else:
    if not all([DB_USERNAME, DB_PASSWORD, DB_SERVER, DB_DATABASE]):
        missing = []
        if not DB_USERNAME:
            missing.append("DB_USERNAME")
        if not DB_PASSWORD:
            missing.append("DB_PASSWORD")
        if not DB_SERVER:
            missing.append("DB_SERVER")
        if not DB_DATABASE:
            missing.append("DB_DATABASE")
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    encoded_password = quote_plus(DB_PASSWORD)
    DATABASE_URL = (
        f"mssql+pyodbc://{DB_USERNAME}:{encoded_password}@{DB_SERVER}/{DB_DATABASE}"
        f"?driver={ODBC_DRIVER.replace(' ', '+')}"
    )

    # Optional: Add additional connection parameters
    # DATABASE_URL += "&TrustServerCertificate=yes"  # For self-signed certificates
    # DATABASE_URL += "&Encrypt=yes"  # For encrypted connections

    logger.info(f"Connecting to SQL Server: {DB_SERVER}/{DB_DATABASE}")

# Create the engine
engine_args = {
    "pool_pre_ping": True,
    "echo": False,
}
if not DATABASE_URL_ENV:
    engine_args["pool_size"] = POOL_SIZE
    engine_args["max_overflow"] = MAX_OVERFLOW

engine = create_engine(DATABASE_URL, **engine_args)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()
