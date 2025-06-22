"""Validate the database connection.

This small helper script imports :func:`src.db.connection.test_connection`
and executes it.  It's intended for local development to quickly verify that
the environment can reach the configured database.  A more robust health
check may be added in the future.
"""

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
