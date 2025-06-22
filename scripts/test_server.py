
"""Launch the local FastAPI server for manual testing.

This script is convenience glue so developers can run ``python scripts/test_server.py``
and start the API without remembering the ``uvicorn`` command. In production the
server is normally started via the package entry points.
"""

__test__ = False  # prevent pytest from collecting this script as a test

from pathlib import Path
import sys

# Ensure the repository root is on ``sys.path`` when imported by pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    """Run the FastAPI application using uvicorn."""

    from src.fastapi_server import main as _run

    _run()


if __name__ == "__main__":  # pragma: no cover - manual utility
    main()

