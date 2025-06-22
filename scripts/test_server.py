"""Run the FastAPI server locally for testing."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.fastapi_server:create_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

