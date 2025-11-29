import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
# FIX 1: Import the text function for raw SQL execution
from sqlalchemy.sql import text 
import redis.asyncio as redis 

from app.core.dependencies import get_db, get_redis_client

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
async def check_health(
    db: Session = Depends(get_db), 
    redis_client: redis.Redis = Depends(get_redis_client) 
):
    """
    Performs a health check on critical services (DB and Redis).
    """
    health_status = {
        "database": False,
        "redis": False,
        "api_status": "UP"
    }

    try:
        # 1. Database Check 
        # FIX 2: Explicitly wrap the raw SQL string with text()
        db.execute(text("SELECT 1"))
        health_status["database"] = True
    except Exception as e:
        logging.getLogger("app").error(f"Database health check failed: {e}")
        
    try:
        # 2. Redis Check (Execute PING command)
        await redis_client.ping()
        health_status["redis"] = True
    except Exception as e:
        logging.getLogger("app").error(f"Redis health check failed: {e}")
        
    # Final Status Check (If any critical service is down, raise 503)
    if not all(health_status.values()):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "Critical services offline", "details": health_status}
        )
        
    return {"message": "All critical services running", "details": health_status}