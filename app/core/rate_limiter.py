import logging
from fastapi import HTTPException, status
from app.config.redis import get_redis

logger = logging.getLogger(__name__)

LUA_SCRIPT = """
local current = redis.call("INCR", KEYS[1])
if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end
return current
"""

RATE_LIMIT = 100
WINDOW = 60

async def rate_limiter(user_id: int, endpoint: str):
    redis = await get_redis()
    key = f"ratelimit:user:{user_id}:{endpoint}"

    try:
        count = await redis.eval(LUA_SCRIPT, 1, key, WINDOW)

        if count > RATE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Rate limiter error for user {user_id}: {e}")
