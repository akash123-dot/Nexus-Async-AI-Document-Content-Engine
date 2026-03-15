from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql_models import UserFileMetadata
from app.schemas.schemas import FileMetadata
from app.repositories.file_repo import UserFileRepository
from fastapi import HTTPException
from .exceptions import NotFoundException, BadRequestException

class UserFileService:
    @staticmethod
    async def user_file_create(
        db: AsyncSession,
        user_id: int,
        user: FileMetadata,
    ) -> UserFileMetadata | None:

        if await UserFileRepository.fetch_user_file_metadata_by_id(db, user_id):
            raise BadRequestException("File already exists please delete it first")
        

        file_create = UserFileMetadata(user_id = user.user_id,
                                       file_name = user.file_name,
                                       file_size = user.file_size,
                                       file_type = user.file_type,
                                       extension = user.extension,
                                       storage_path = user.storage_path
                                       )
        
        await UserFileRepository.user_file_create(db, file_create)
        await db.commit()
        await db.refresh(file_create)
        return file_create
    

    @staticmethod
    async def fetch_user_file_metadata_by_id(
        db: AsyncSession,
        user_id: int,
    ) -> UserFileMetadata | None:
        
        return await UserFileRepository.fetch_user_file_metadata_by_id(db, user_id)
    

    @staticmethod
    async def fetch_user_file_metadata(
        db: AsyncSession,
        user_id: int,
    ):
        return await UserFileRepository.fetch_user_file_metadata(db, user_id)


    @staticmethod
    async def delete_user_file_metadata(
        db: AsyncSession,
        user_id: int,
    ):
        result = await UserFileRepository.delete_user_file_metadata(db, user_id)
        if result.rowcount == 0:
            raise NotFoundException("File not found")
        
        await db.commit()

        return result