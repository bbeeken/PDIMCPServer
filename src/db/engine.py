"""Database engine configuration."""

import os
import logging
from urllib.parse import quote_plus

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

# Load environment variables from a .env file if present
load_dotenv()

# Get environment variables
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
ODBC_DRIVER = os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
POOL_SIZE = int(os.getenv("POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("MAX_OVERFLOW", "20"))

# Validate required environment variables
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
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# URL-encode password to handle special characters
encoded_password = quote_plus(DB_PASSWORD)

# Construct the database URL properly
DATABASE_URL = (
    f"mssql+pyodbc://{DB_USERNAME}:{encoded_password}@{DB_SERVER}/{DB_DATABASE}"
    f"?driver={ODBC_DRIVER.replace(' ', '+')}"
)

# Optional: Add additional connection parameters
# DATABASE_URL += "&TrustServerCertificate=yes"  # For self-signed certificates
# DATABASE_URL += "&Encrypt=yes"  # For encrypted connections

logger.info(f"Connecting to SQL Server: {DB_SERVER}/{DB_DATABASE}")

# Create the engine
engine = create_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    echo=False,  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()
