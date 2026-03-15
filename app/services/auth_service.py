from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.sql_models import AuthUser
from app.core.security import hash_password
from app.repositories.auth_repo import AuthUserRepository
from app.core.jwt import create_access_token, create_refresh_token
from app.core.store_token_redis import store_refresh_token
from .exceptions import UserAlreadyExistsError
# from fastapi import HTTPException, status

class AuthUserService:
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
    ) -> AuthUser:
        
        # existing_user = await AuthUserRepository.get_by_UserNameAndEmail(db, username, email)
        # if existing_user:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="User already exists"
        #     )

        
        user = AuthUser(
            username=username,
            email=email,
            hashed_password= await hash_password(password),
        )

        try:
            await AuthUserRepository.CreateUser(db, user)

            await db.commit()
        # await db.refresh(user)
        except IntegrityError:
            raise UserAlreadyExistsError("User already exists")


        return user

    @staticmethod
    async def login_survice(
        db: AsyncSession,
        username: str,
        # email: str,
        password: str,
    ) -> dict:
        
        user = await AuthUserRepository.login(db, username, password)

        if not user:
            raise ValueError("Invalid credentials")
        create_token = create_access_token(subject=str(user.id))
        refresh_token, jti = create_refresh_token(subject=str(user.id))

        await store_refresh_token(str(user.id), jti)

        return {"access_token": create_token, "refresh_token": refresh_token}


