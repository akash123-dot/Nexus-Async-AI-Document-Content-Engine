from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.sql_models import AuthUser
from app.core.security import verify_password

class AuthUserRepository:

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        user_id: int,
    ) -> AuthUser | None:
        stmt = select(AuthUser).where(AuthUser.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_UserNameAndEmail(
        db: AsyncSession,
        username: str,
        email: str,
    ) ->AuthUser | None:
        stmt = select(AuthUser).where(
            or_(
                AuthUser.username == username,
                AuthUser.email == email,
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def CreateUser(
        db: AsyncSession,
        user: AuthUser,
    ) ->AuthUser:

        db.add(user)
        # await db.flush()
        return user
    
    @staticmethod
    async def login(
        db: AsyncSession,
        username: str,
        # email: str,
        password: str,
    ) ->AuthUser | None:

        stmt = select(AuthUser).where(AuthUser.username == username,)
        result = await db.execute(stmt)
  
        user = result.scalar_one_or_none()
        if user and await verify_password(password, user.hashed_password):
            return user

        return None

                