from app.config.redis import get_redis
from dotenv import load_dotenv
import os
load_dotenv()

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))

async def store_refresh_token(user_id: str, jti: str):

    redis = await get_redis()

    key = f"refresh_token:{user_id}:{jti}"
    ttl = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    await redis.set(key, "1", ex=ttl)


async def get_refresh_token(user_id: str, jti: str):

    redis = await get_redis()

    key = f"refresh_token:{user_id}:{jti}"

    return await redis.exists(key)



async def delete_refresh_token(user_id: str, jti: str):

    redis = await get_redis()

    key = f"refresh_token:{user_id}:{jti}"

    return await redis.delete(key)