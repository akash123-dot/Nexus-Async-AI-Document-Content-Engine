from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.content_gen_repo import UserContentGenRepository, ContentTaskRepository
from app.schemas.content_gen_schemas import ContentGenerationMetadata, TaskOut, TaskListResponse
from app.models.sql_models import ContentGenerationTask
from typing import Optional
from fastapi import HTTPException
# from repository import ContentTaskRepository


class ContentGenerationService:
    @staticmethod
    async def create_content_task(
        db: AsyncSession,
        task: ContentGenerationMetadata,
    ):
        
        data = ContentGenerationTask(unique_task_id=task.unique_task_id, user_id=task.user_id, task_type=task.task_type, question=task.question)
      
        await UserContentGenRepository.create_content_task(db, data)
        await db.commit()
        # await db.refresh(task)
        return task
    

    @staticmethod
    async def update_content_task(
        db: AsyncSession,
        task_status: str,
        task_result: str,
        unique_task_id: str,
        user_id: int,
    ):
        task = await UserContentGenRepository.update_content_task(
            db, task_status, task_result, unique_task_id, user_id
        )

        if task == 0:
            raise HTTPException(status_code=404, detail="Task not found")

        await db.commit()
    
        return task
    


    @staticmethod
    async def view_content_task(
        db: AsyncSession,
        unique_task_id: str,
        user_id: int,
    ):
        result = await UserContentGenRepository.view_content_task(db, unique_task_id, user_id)

        if result is None:
            raise HTTPException(status_code=404, detail="Task not found")

        return result


    @staticmethod
    async def delete_content_task(
        db: AsyncSession,
        unique_task_id: str,
        user_id: int,
    ):
        try:
            result = await UserContentGenRepository.delete_content_task(db, unique_task_id, user_id)
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Task not found")
            
            await db.commit()
        except Exception as e:
            raise e

        return 
        
    @staticmethod
    async def delete_all_content_task(
        db: AsyncSession,
        user_id: int,
    ):
        try:
            result = await UserContentGenRepository.delete_all_content_task(db, user_id)
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Task not found")
            


            await db.commit()
        except Exception as e:
            raise e

        return

class ContentTaskService:

    def __init__(self, db: AsyncSession):
        self.repo = ContentTaskRepository(db)

    async def list_user_tasks(
        self,
        user_id: int,
        limit: int,
        cursor: Optional[str],
    ) -> TaskListResponse:

        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100.")

        tasks, next_cursor = await self.repo.get_tasks_page(
            user_id=user_id,
            limit=limit,
            cursor=cursor,
        )

        return TaskListResponse(
            data=[TaskOut.model_validate(t) for t in tasks],
            next_cursor=next_cursor,
            has_next=next_cursor is not None,
        )








