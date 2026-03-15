from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_async_session
from app.core.dependencies import get_current_user
from app.models.sql_models import AuthUser
from app.core.rate_limiter import rate_limiter
from app.schemas.content_gen_schemas import( ContentGenerationConfig, TaskOut,
                                             ContentGenerationMetadata, TaskListResponse,
                                             SingleTaskResponse)

from app.services.content_gen_service import ContentGenerationService
# from fastapi.encoders import jsonable_encoder
from app.messaging.publisher import publish_user_task
from typing import Optional
from datetime import datetime
import uuid
# import json

router = APIRouter(prefix="/content_generation", tags=["Content Gen"])


@router.post("/generate_content", status_code=status.HTTP_200_OK)
async def generate_content(
    request: Request,
    data: ContentGenerationConfig = Body(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthUser = Depends(get_current_user),
):
    await rate_limiter(
        user_id = current_user.id,
        endpoint = request.url.path
    )



   
    metadata = ContentGenerationMetadata(
        unique_task_id=str(uuid.uuid4()),
        user_id=current_user.id,
        question=data.topic,
        task_type="content_generation",
    )

    service = await ContentGenerationService.create_content_task(db, metadata)

    # print("Service:", service)
    # print("*" * 100)

    unique_task_id = service.unique_task_id
    user_id = service.user_id
    task_type = service.task_type

    payload = ContentGenerationConfig.model_validate(data).model_dump()

    payload["user_id"] = user_id
    payload["unique_task_id"] = unique_task_id
    # payload["task_type"] = task_type
    
    # print("Payload:", payload)

    await publish_user_task(user_id=current_user.id, task_type=task_type, payload=payload)

    return {"unique_task_id": unique_task_id}


   



@router.post("/generate_content/view_content", status_code=status.HTTP_200_OK, response_model=SingleTaskResponse)
async def view_content(
    request: Request,
    unique_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthUser = Depends(get_current_user),
):
    
    await rate_limiter(
        user_id = current_user.id,
        endpoint = request.url.path
    )

    # print("current user id:", current_user.id)
   
    service = await ContentGenerationService.view_content_task(db, unique_id, current_user.id)

    return service

  

   
@router.delete("/generate_content/delete_content", status_code=status.HTTP_200_OK)
async def delete_content(
    request: Request,
    unique_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthUser = Depends(get_current_user),
):
    

    await rate_limiter(
        user_id = current_user.id,
        endpoint = request.url.path
    )



    service = await ContentGenerationService.delete_content_task(db, unique_id, current_user.id)

    return service





@router.delete("/generate_content/delete_all_content", status_code=status.HTTP_200_OK)
async def delete_all_content(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthUser = Depends(get_current_user),
):
    

    await rate_limiter(
        user_id = current_user.id,
        endpoint = request.url.path
    )

   
    await ContentGenerationService.delete_all_content_tasks(db, current_user.id)


    return {"message": "Content deleted successfully"}

  


@router.get("/list_content_tasks", status_code=status.HTTP_200_OK)
async def list_content_tasks(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    cursor: datetime | None = Query(None),
    cursor_id: int | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthUser = Depends(get_current_user),
):
    
    await rate_limiter(
        user_id = current_user.id,
        endpoint = request.url.path
    )
    # print("current user id:", current_user.id)
    
    service = await ContentGenerationService.list_content_task(db, current_user.id, limit, cursor, cursor_id)

    return service


    



        