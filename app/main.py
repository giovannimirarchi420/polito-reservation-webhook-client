from fastapi import FastAPI
import uvicorn

from . import config
from .api import router

# Create FastAPI app
app = FastAPI(
    title="Resource Webhook Client",
    description="Service to handle webhook events for resource reservation",
    version="1.0.0",
)

# Add router to the FastAPI application
app.include_router(router)

# When run directly, this will start the server
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # Bind to all interfaces
        port=config.PORT,
        reload=False
    )