from fastapi import FastAPI
from app.api import auth, file_tools, image_tools, status
from app.db.database import create_db_tables
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings, configure_logging
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from app.core.dependencies import get_redis_client

# Initialize FastAPI application
app = FastAPI(
    title="Day-to-Day Utility Backend",
    description="Backend for file and image processing tools with JWT security.",
    version="1.0.0",
)
#configure_logging()
origins = settings.CORS_ALLOWED_ORIGINS.split(',') if settings.CORS_ALLOWED_ORIGINS else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # 1. Create the async Redis client instance from the connection URL
    redis_client = get_redis_client() 
    # 2. Test the connection
    try:
        await redis_client.ping()
        print("✅ Redis connection established and PONG received.")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        
    # 3. Initialize the FastAPILimiter with the client
    await FastAPILimiter.init(redis_client)

# Run this once on startup to ensure tables exist
# In production, use migrations (Alembic) instead
# create_db_tables() 

# Include all the API routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(file_tools.router, prefix="/tools/files", tags=["File & Base64"])
app.include_router(image_tools.router, prefix="/tools/images", tags=["Image Processing"])
app.include_router(status.router, prefix="/status", tags=["Monitoring"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Utility API. Navigate to /docs for interactive documentation."}