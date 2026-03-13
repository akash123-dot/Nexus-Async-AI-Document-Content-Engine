from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_async_session
from app.core.dependencies import get_current_user
from app.models.sql_models import AuthUser
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.schemas import BlueskyConnectRequest, PostRequest
from app.services.bluesky_services import BlueskyServices
from app.core.rate_limiter import rate_limiter
from app.core.security import decrypt_password

router = APIRouter(prefix="/social", tags=["social"])

BLUESKY_API = "https://bsky.social/xrpc"



async def create_bluesky_session(handle: str, app_password: str) -> dict:
  
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BLUESKY_API}/com.atproto.server.createSession",
            json={
                "identifier": handle,    
                "password": app_password 
            }
        )

    if response.status_code == 401:
        raise HTTPException(
            status_code=401,
            detail="Invalid Bluesky handle or app password. Make sure you're using an App Password, not your main account password[settings -> privacy-and-security -> app-password]."
        )

    if not response.is_success:
        raise HTTPException(
            status_code=502,
            detail=f"Bluesky auth error: {response.text}"
        )

    return response.json()  




@router.post("/auth/bluesky/connect")
async def connect_bluesky(
    request: Request,
    body: BlueskyConnectRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    
    await rate_limiter(
        user_id = current_user.id,
        endpoint = request.url.path
    )

    try:
        await create_bluesky_session(body.handle, body.app_password)

        service = BlueskyServices(db)

        result = await service.fetch_bluesky_account(
            current_user.id,
            "bluesky",
            body.handle,
            body.app_password
        )

        if not result:
            raise HTTPException(
                status_code=400,
                detail="Failed to connect Bluesky account"
            )

        return {
            "message": f"Bluesky account @{body.handle} connected successfully."
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/post/bluesky")
async def post_to_bluesky(
    request: Request,
    content: PostRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    
    await rate_limiter(
        user_id = current_user.id,
        endpoint = request.url.path
    )

    service = BlueskyServices(db)
   
    result = await service.prepare_bluesky_post(current_user.id)

    if not result:
        raise HTTPException(
            status_code=401,
            detail="Bluesky account not connected. POST to /social/auth/bluesky/connect first."
        )
    
    try:
        password = decrypt_password(result.app_password)

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid password."
        )


    session = await create_bluesky_session(result.handle, password)

    access_jwt = session["accessJwt"]
    did = session["did"]  

    
    if len(content.text) > 300:
        raise HTTPException(
            status_code=400,
            detail=f"Post too long. Bluesky max is 300 characters, yours is {len(content.text)}."
        )


    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BLUESKY_API}/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {access_jwt}"},
            json={
                "repo": did,                        
                "collection": "app.bsky.feed.post", 
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": content.text,
                    "createdAt": datetime.now(timezone.utc).isoformat(), 
                }
            }
        )

    if response.status_code == 429:
        raise HTTPException(status_code=429, detail="Bluesky rate limit hit. Try again shortly.")

    if not response.is_success:
        raise HTTPException(
            status_code=502,
            detail=f"Bluesky post error {response.status_code}: {response.text}"
        )

    data = response.json()

    return {
        "message": "Posted to Bluesky successfully.",
        "uri": data.get("uri"),   
        "cid": data.get("cid"),   
    }



@router.delete("/auth/bluesky/disconnect")
async def disconnect_bluesky(
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    
    await rate_limiter(
        user_id = current_user.id,
        endpoint = request.url.path
    )
    
    service = BlueskyServices(db)

    result = await service.disconnect_bluesky(current_user.id)

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Failed to disconnect Bluesky account"
        )
    
    return result