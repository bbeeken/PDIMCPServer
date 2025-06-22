"""
Database connection management
"""
import os
import logging
from typing import Optional, Any
from contextlib import contextmanager
import pyodbc
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'server': os.getenv('DB_SERVER'),
    'database': os.getenv('DB_DATABASE', 'PDI_Warehouse_1539_01'),
    'username': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'driver': os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')
}

# Connection pool
_connection_pool = []
MAX_POOL_SIZE = 5

def get_connection_string() -> str:
    """Build connection string from config"""
    return (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"TrustServerCertificate=yes;"
    )

@contextmanager
def get_connection():
    """Get a database connection from the pool"""
    conn = None
    try:
        # Try to get from pool
        if _connection_pool:
            conn = _connection_pool.pop()
            # Test if connection is still alive
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            except:
                conn.close()
                conn = None
        
        # Create new connection if needed
        if conn is None:
            conn = pyodbc.connect(get_connection_string())
            conn.autocommit = False
        
        yield conn
        
        # Return to pool if room
        if len(_connection_pool) < MAX_POOL_SIZE:
            _connection_pool.append(conn)
            conn = None
            
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def execute_query(sql: str, params: Optional[list] = None) -> list:
    """Execute a query and return results"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        # Get column names
        columns = [column[0] for column in cursor.description] if cursor.description else []
        
        # Fetch all results
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        cursor.close()
        return results

def test_connection() -> bool:
    """Test database connection"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            cursor.close()
            return result[0] == 1
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False