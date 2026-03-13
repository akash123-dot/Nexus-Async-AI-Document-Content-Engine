import asyncio
from redis.asyncio import Redis
from app.config.settings import settings
redis: Redis | None = None

async def init_redis() ->None:
    global redis
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
        max_connections=settings.REDIS_MAX_CONNECTIONS,  
    )

async def close_redis() -> None:
    if redis:
        await redis.close()

async def get_redis() ->Redis:
    if not redis:
        raise RuntimeError("Redis is not initialized")
    return redis