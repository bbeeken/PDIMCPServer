#!/usr/bin/env python3
"""
Script to generate the folder and file structure for the 'mcp-pdi-server' project.
Run this script from the directory where you want 'mcp-pdi-server' to be created.
"""

from pathlib import Path

# Define the project structure: folders mapped to their files
structure = {
    "": [
        ".env.example",
        ".gitignore",
        "README.md",
        "requirements.txt",
        "setup.py",
        "pyproject.toml",
        "package.json",
        "mcp_server.py",
    ],
    "src": [
        "__init__.py",
        "server.py",
    ],
    "src/db": [
        "__init__.py",
        "connection.py",
        "models.py",
    ],
    "src/tools": [
        "__init__.py",
        "utils.py",
    ],
    "src/tools/sales": [
        "__init__.py",
        "query_realtime.py",
        "sales_summary.py",
        "sales_trend.py",
        "top_items.py",
    ],
    "src/tools/basket": [
        "__init__.py",
        "basket_analysis.py",
        "item_correlation.py",
        "basket_metrics.py",
        "cross_sell.py",
    ],
    "src/tools/analytics": [
        "__init__.py",
        "hourly_sales.py",
        "peak_hours.py",
        "product_velocity.py",
        "sales_anomalies.py",
    ],
    "src/tests": [
        "__init__.py",
        "test_connection.py",
        "test_tools.py",
    ],
    "scripts": [
        "validate_db.py",
        "test_server.py",
    ],
}


def create_project_structure(base_name: str):
    base_path = Path(base_name)
    for folder, files in structure.items():
        dir_path = base_path / folder
        dir_path.mkdir(parents=True, exist_ok=True)
        for filename in files:
            file_path = dir_path / filename
            file_path.touch(exist_ok=True)
    print(f"Project structure for '{base_name}' has been created.")


if __name__ == "__main__":
    create_project_structure("mcp-pdi-server")
