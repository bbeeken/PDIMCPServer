"""Validate database connectivity."""

from src.db.connection import test_connection

if __name__ == "__main__":
    if test_connection():
        print("Database connection successful.")
    else:
        print("Database connection failed.")

