from passlib.context import CryptContext
import anyio
# from fastapi.concurrency import run_in_threadpool
import hashlib
import base64
import secrets
import json
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=10, deprecated="auto")
bcrypt_limiter = anyio.CapacityLimiter(10)


async def hash_password(password: str) -> str:
    # return pwd_context.hash(password)
    return await anyio.to_thread.run_sync(pwd_context.hash, password, limiter=bcrypt_limiter)

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    # return pwd_context.verify(plain_password, hashed_password)
    return await anyio.to_thread.run_sync(
        lambda: pwd_context.verify(plain_password, hashed_password), limiter=bcrypt_limiter
    )





def encode_cursor(task_id: int, created_at: datetime) -> str:
   
    payload = {"id": task_id, "created_at": created_at.isoformat()}
    json_bytes = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(json_bytes).decode("utf-8")


def decode_cursor(cursor: str) -> tuple[int, datetime]:
    
    try:
        json_bytes = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        payload = json.loads(json_bytes)
        return payload["id"], datetime.fromisoformat(payload["created_at"])
    except Exception:
        raise ValueError("Invalid or tampered cursor token.")