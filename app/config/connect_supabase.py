from supabase import create_async_client, AsyncClient
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

_supabase: AsyncClient | None = None


async def get_supabase_client() -> AsyncClient:
    global _supabase
    if _supabase is None:
        _supabase = await create_async_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    return _supabase
