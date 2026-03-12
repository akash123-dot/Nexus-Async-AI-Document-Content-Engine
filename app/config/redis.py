import asyncio
from redis.asyncio import Redis

redis: Redis | None = None

async def init_redis() ->None:
    global redis
    redis = Redis(
        host="redis",
        port=6379,
        decode_responses=True,
        max_connections=20,  
    )

async def close_redis() -> None:
    if redis:
        await redis.close()

async def get_redis() ->Redis:
    if not redis:
        raise RuntimeError("Redis is not initialized")
    return redis