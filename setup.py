from setuptools import setup, find_packages

setup(
    name="mcp-pdi-server",
    version="1.0.0",
    description="MCP server for PDI sales analytics",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.9.4",
        "pyodbc>=5.0.1",
        "pandas>=2.1.4",
        "numpy>=1.26.2",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
)
