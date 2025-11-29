# app/core/redis_client.py

import redis.asyncio as redis
from typing import Optional

# This variable will hold the initialized Redis client instance.
# It starts as None and gets set during application startup.
redis_client: Optional[redis.Redis] = None