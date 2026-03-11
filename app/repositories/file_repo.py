from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, delete
from app.models.sql_models import UserFileMetadata
from app.schemas.schemas import FileMetadata


class UserFileRepository:
    @staticmethod
    async def user_file_create(
        db: AsyncSession,
        user_file: UserFileMetadata,    
    ) -> UserFileMetadata | None:
        
        db.add(user_file)
        # await db.flush()
        return user_file
    

    @staticmethod
    async def fetch_user_file_metadata_by_id(
        db: AsyncSession,
        user_id: int,
    ) -> UserFileMetadata | None:
        
        result = await db.execute(
            select(UserFileMetadata.id).where(UserFileMetadata.user_id == user_id).order_by(UserFileMetadata.created_at.desc()).limit(1)
        )

        return result.scalar_one_or_none()
    

    @staticmethod
    async def fetch_user_file_metadata(
        db: AsyncSession,
        user_id: int,
    ):
        
        result = await db.execute(
            select(UserFileMetadata.id, UserFileMetadata.storage_path).where(UserFileMetadata.user_id == user_id)
        )

        return result.one_or_none()
    

    @staticmethod
    async def delete_user_file_metadata(
        db: AsyncSession,
        user_id: int,
    ):
       
        
        result = await db.execute(
            delete(UserFileMetadata).where(UserFileMetadata.user_id == user_id)
        )

        return result