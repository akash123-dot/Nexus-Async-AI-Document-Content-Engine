from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_async_session
from app.services.auth_service import AuthUserService, UserAlreadyExistsError
from app.schemas.schemas import SignUpSchema, TokenResponse, LoginSchema
from app.core.jwt import decode_token, create_access_token
from app.core.store_token_redis import get_refresh_token, delete_refresh_token






router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: SignUpSchema,
    db: AsyncSession = Depends(get_async_session),
):
    try:
        user = await AuthUserService.create_user(
            db=db,
            username=data.username,
            email=data.email,
            password=data.password,
        )

        # return {
        #     "id": user.id,
        #     "username": user.username,
        #     "email": user.email,
        #     "message": "User registered successfully",
        # }
        return { "message": "User registered successfully", "user": user }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    
@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginSchema,
    db: AsyncSession = Depends(get_async_session),
):
    try:
        token = await AuthUserService.login_survice(
            db=db,
            username=data.username,
            # email=data.email,
            password=data.password,
        )
        return {
            "access_token": token["access_token"],
            "refresh_token": token["refresh_token"],
            "token_type": "bearer",
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    



@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: str = Body(...),
    # db: AsyncSession = Depends(get_async_session),
):
    try:
        decoded_token = decode_token(payload)
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )
    
    if decoded_token["type"] != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )
    
    user_id = decoded_token["sub"]
    jti = decoded_token["jti"]

    key = await get_refresh_token(user_id, jti)

    if not key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    new_access_token = create_access_token(user_id)
    return {
        "access_token": new_access_token,
        "refresh_token": payload,
        "token_type": "bearer",
    }



@router.post("/logout")
async def logout(
    payload:str = Body(...),
):
    try:
        decoded_token = decode_token(payload)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )
    
    if decoded_token["type"] != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )
    
    user_id = decoded_token["sub"]
    jti = decoded_token["jti"]

    await delete_refresh_token(user_id, jti)

    return {"message": "Logged out successfully"}


