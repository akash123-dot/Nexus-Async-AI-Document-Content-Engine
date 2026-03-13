from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_async_session
from pathlib import Path
from app.models.sql_models import AuthUser
from app.core.dependencies import get_current_user
# from app.config.redis import get_redis
from app.core.rate_limiter import rate_limiter
from app.services.file_services import UserFileService
from app.schemas.schemas import FileMetadata, UserFileOut, RetrieveAnswerSchema
from supabase import AsyncClient
from app.config.connect_supabase import get_supabase_client
from app.messaging.publisher import publish_user_task
from typing import Annotated
# from io import BytesIO
from fastapi.encoders import jsonable_encoder
from app.rag.retrive_answer.retrive_answers import generate_answer
from app.rag.delete_vectordb import delete_user_database
from app.config.settings import settings
from app.config.redis import get_redis
# import magic
import uuid
# import os
# from dotenv import load_dotenv

# load_dotenv()



router = APIRouter(prefix="/files", tags=["Files"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".doc", ".docx"}

MAX_FILE_SIZE = 10 * 1024 * 1024

BUCKET_NAME = settings.BUCKET_NAME



@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    request: Request,
    # file: UploadFile = File(...),
    file: Annotated[UploadFile, File(...)],
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthUser = Depends(get_current_user),
    supabase: AsyncClient = Depends(get_supabase_client),
):
    redis = await get_redis()


    await rate_limiter(
        user_id = current_user.id,
        endpoint = request.url.path
    )
    
    # if file.content_type not in ALLOWED_MIME_TYPES:
    #     raise HTTPException(
    #         status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    #         detail="Unsupported file type",
    #     )
    
    exe = Path(file.filename).suffix.lower()
    if exe not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file extension",
        )
    
    file_content = await file.read()
    # file_stream = BytesIO(file_content)
    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size is too large",
        )
    
    file_id = str(uuid.uuid4())
    unique_file_name = f"{file_id}{exe}"
    storage_path = f"folder/{unique_file_name}"

    try:
        await supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": file.content_type},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    
    # print(file.content_type, unique_file_name, file_size, exe, storage_path)

    try:
        file_metadata = FileMetadata(
            user_id=current_user.id,
            file_name=unique_file_name,
            file_size=file_size,
            file_type=file.content_type or "application/octet-stream",
            extension=exe,
            storage_path=storage_path
        )

        responce = await UserFileService.user_file_create(db=db, user_id=current_user.id, user = file_metadata)

        # payload = UserFileOut.model_validate(responce).model_dump()
        payload = jsonable_encoder(UserFileOut.model_validate(responce))

        await publish_user_task(user_id=current_user.id, task_type="file_processing", payload=payload)

        redis.set(file_id, "processing", ex=600)

        return responce
    
    except Exception as e:
        await supabase.storage.from_(BUCKET_NAME).remove([storage_path])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    

@router.post("/upload/status", status_code=status.HTTP_201_CREATED)
async def upload_status(
    unique_file_name: str = Body(...),
    # db: AsyncSession = Depends(get_async_session),
    # current_user: AuthUser = Depends(get_current_user),
):

    redis = await get_redis()

    status = await redis.get(unique_file_name)
    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found or expired",
        )
    
    return status



## Retrieve Answer from Vector DB

@router.post("/retrieve_answer", status_code=status.HTTP_200_OK)
async def retrieve_answer(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthUser = Depends(get_current_user),
    data: RetrieveAnswerSchema = Body(...),
):
    await rate_limiter(
        user_id = current_user.id,
        endpoint = request.url.path
    )

    file_info = await UserFileService.fetch_user_file_metadata_by_id(db=db, user_id=current_user.id)

    # here we cache the file information
    if not file_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


    user_id = current_user.id
    file_id = file_info
    # file_name = file_info.file_name
    question = data.question

    answer = await generate_answer(question=question,
                                  user_id=user_id,
                                  file_id=file_id,
                                  )

    return answer




@router.delete("/delete/delete_file_data", status_code=status.HTTP_200_OK)
async def delete_file_data(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthUser = Depends(get_current_user),
    supabase: AsyncClient = Depends(get_supabase_client),
):
    await rate_limiter(
        user_id = current_user.id,
        endpoint = request.url.path
    )
    
    user_file_data = await UserFileService.fetch_user_file_metadata(db=db, user_id=current_user.id)

    if not user_file_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    user_id = current_user.id
    file_id = user_file_data.id
    storage_path = user_file_data.storage_path

    try:
        await delete_user_database(user_id=user_id, file_id=file_id)
        await supabase.storage.from_(BUCKET_NAME).remove([storage_path])
        await UserFileService.delete_user_file_metadata(db=db, user_id=user_id)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return {"message": "File deleted successfully"}