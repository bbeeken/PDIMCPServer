"""Basic smoke test for server initialization."""

__test__ = False  # prevent pytest from collecting this script as a test

from pathlib import Path
import sys

# Ensure the repository root is on ``sys.path`` when imported by pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.mcp_server import create_server


def main() -> None:
    """Instantiate the MCP server and report a short status."""
    server = create_server()
    print(f"Loaded server '{server.name}' with {len(server.tools)} tools")


if __name__ == "__main__":  # pragma: no cover - manual utility
    main()
