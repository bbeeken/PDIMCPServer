"""Validate the database connection."""

__test__ = False  # prevent pytest from collecting this script as a test

from src.db.connection import test_connection


def main() -> None:
    """Run the connection test and print the result."""

    if test_connection():
        print("Database connection successful")
    else:
        print("Database connection failed")
        raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover - manual utility
    main()
