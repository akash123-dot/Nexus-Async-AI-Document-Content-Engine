from supabase import create_async_client, AsyncClient
from app.config.settings import settings
# import os
# from dotenv import load_dotenv

# load_dotenv()

SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY

_supabase: AsyncClient | None = None


async def get_supabase_client() -> AsyncClient:
    global _supabase
    if _supabase is None:
        _supabase = await create_async_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    return _supabase
