from fastapi import FastAPI
import os
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import logging # Import logging
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from admin_app.core.vite import register_vite_env # Import the vite helper registration
from admin_app.core.system_tags import sync_system_tags # Import the sync function

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
    Runs system tag synchronization after DB connection.
    """
    try:
        app.state.mongo_client = AsyncIOMotorClient(MONGO_URI)
        # The ismaster command is cheap and does not require auth.
        await app.state.mongo_client.admin.command('ismaster')
        app.state.mongo_db = app.state.mongo_client[MONGO_DATABASE]
        logger.info("MongoDB connection established.")

        # Run system tag synchronization
        logger.info("Running system tag synchronization...")
        await sync_system_tags(app.state.mongo_db)
        logger.info("System tag synchronization finished.")

    except Exception as e:
        logger.error(f"Error during application startup (DB connection or tag sync): {e}")
        # Optionally re-raise or handle differently to prevent app start?
        # For now, just log the error.
        app.state.mongo_client = None
        app.state.mongo_db = None

    yield # Application runs here

    if app.state.mongo_client:
        app.state.mongo_client.close()
        logger.info("MongoDB connection closed.")

# --- Logging Configuration --- Start ---
log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
date_fmt = '%Y-%m-%d %H:%M:%S'

root_logger = logging.getLogger() # Get root logger
root_logger.setLevel(logging.DEBUG) # Keep root logger level at DEBUG

# Clear existing handlers (important if using reload)
if root_logger.hasHandlers():
    root_logger.handlers.clear()

# Console Handler (DEBUG level)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO) # <--- CHANGED FROM INFO TO DEBUG
console_formatter = logging.Formatter(log_fmt, datefmt=date_fmt)
console_handler.setFormatter(console_formatter)
root_logger.addHandler(console_handler)

# Optionally set specific library loggers to WARNING or ERROR if needed
# logging.getLogger("pymongo").setLevel(logging.WARNING)
# logging.getLogger("uvicorn").setLevel(logging.INFO)

logger.info("Logging configured: Console=DEBUG+") # <--- UPDATED INFO MESSAGE
# --- Logging Configuration --- End ---

app = FastAPI(
    title="Admin Panel API",
    description="API for managing articles and images.",
    version="0.1.0",
    lifespan=lifespan
)

# Mount the static directory for Vite's output BEFORE including routers that might depend on templates
app.mount("/static/admin_dist", StaticFiles(directory="admin_app/static/admin_dist"), name="admin_static_dist")

# --- Jinja2 Templates Setup ---
# Create templates instance BEFORE routers need it
templates = Jinja2Templates(directory="admin_app/frontend/templates")

# Register the vite_tags helper
register_vite_env(templates.env)

# Dependency function to provide the configured templates instance
def get_templates() -> Jinja2Templates:
    return templates
# -----------------------------

"""
Centralized router inclusion:
- CRUD routes for articles are included from admin_app/routes/articles.py.
- Image endpoints are included from admin_app/routes/images.py.
"""
from admin_app.routes import articles
from admin_app.routes import images
from admin_app.routes import auth
from admin_app.routes import admin_ui # This will now use the configured templates via Depends
from admin_app.routes import tags # Import the new tags router

app.include_router(auth.router, prefix="/api/admin", tags=["Auth"])
app.include_router(articles.router, prefix="/api/admin", tags=["Articles"])
app.include_router(images.router, prefix="/api/admin", tags=["Images"])
app.include_router(tags.router, prefix="/api/admin", tags=["Tags"]) # Add the tags router
app.include_router(admin_ui.router)

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
