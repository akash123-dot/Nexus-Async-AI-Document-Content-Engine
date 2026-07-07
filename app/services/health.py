# app/services/health.py
import httpx
from sqlalchemy import text
from app.config.database import AsyncSessionLocal
from app.config.redis import get_redis
from app.config.settings import settings

async def check_infrastructure_health() -> bool:

    try:
        # Test Postgres 
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        
        # Test Redis
        redis = await get_redis()
        await redis.ping()
        
        # Test Supabase 
        supabase_url = getattr(settings, "SUPABASE_URL", None)
        if supabase_url:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{supabase_url}/rest/v1/")
                if response.status_code >= 500:
                    return False

        return True
        
    except Exception as health_err:
        print(f"CIRCUIT BREAKER ALERT: Infrastructure Health Check Failed! Error: {health_err}")
        return False