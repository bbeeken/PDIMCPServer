"""Basic smoke test for server initialization."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mcp_server import create_server

if __name__ == "__main__":
    server = create_server()
    print(f"Loaded server '{server.name}' with {len(server.tools)} tools")
