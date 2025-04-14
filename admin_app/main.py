from fastapi import FastAPI
import os
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import logging # Import logging

"""
Architectural decision:
- MongoDB connection is implemented using motor (async driver).
- MongoDB client is created on application startup and closed on shutdown.
- Environment variables are used for URI and database name.
- The client is exported via app.state for use in routers.
- All connection parameters are centralized and documented.
"""

logger = logging.getLogger(__name__) # Get logger instance

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/mydatabase")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "mydatabase")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI application lifespan context.
    Initializes and closes the MongoDB client.
    """
    try:
        app.state.mongo_client = AsyncIOMotorClient(MONGO_URI)
        # The ismaster command is cheap and does not require auth.
        await app.state.mongo_client.admin.command('ismaster')
        app.state.mongo_db = app.state.mongo_client[MONGO_DATABASE]
        logger.info("MongoDB connection established.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Optionally re-raise or handle differently to prevent app start?
        # For now, just log the error.
        app.state.mongo_client = None
        app.state.mongo_db = None

    yield # Application runs here

    if app.state.mongo_client:
        app.state.mongo_client.close()
        logger.info("MongoDB connection closed.")

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Admin Panel API",
    description="API for managing articles and images.",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/", tags=["Root"])
async def read_root():
    """ Basic root endpoint to check if the API is running. """
    return {"message": "Admin Panel API is running!"}

"""
Centralized router inclusion:
- CRUD routes for articles are included from admin_app/routes/articles.py.
- Image endpoints are included from admin_app/routes/images.py.
"""
from admin_app.routes import articles
from admin_app.routes import images

app.include_router(articles.router, prefix="/admin", tags=["Articles"])
app.include_router(images.router, prefix="/admin", tags=["Images"])

# Example usage of the client in endpoints:
# from fastapi import Request
# @app.get("/some_path")
# async def some_endpoint(request: Request):
#     db = request.app.state.mongo_db
#     if not db:
#         raise HTTPException(status_code=503, detail="Database not available")
#     # ... use db ...

if __name__ == "__main__":
    import uvicorn
    # This part is mainly for local development without docker/uvicorn command
    logger.info("Starting Uvicorn server locally...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) # Use reload for development
