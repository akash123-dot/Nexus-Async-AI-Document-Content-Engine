from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql_models import ContentGenerationTask
from sqlalchemy import select, or_, and_, update, delete
from app.core.security import decode_cursor, encode_cursor
from typing import Optional
# from app.schemas.content_gen_schemas import ContentGenerationMetadata

class UserContentGenRepository:
    @staticmethod
    async def create_content_task(
        db: AsyncSession,
        task: ContentGenerationTask,
    ) -> ContentGenerationTask | None:
        
        db.add(task)
        
        return task


    @staticmethod
    async def update_content_task(
        db: AsyncSession,
        task_status: str,
        task_result: str,
        unique_task_id: str,
        user_id: int,
    ):
        stmt = (
            update(ContentGenerationTask)
            .where(
                and_(
                    ContentGenerationTask.unique_task_id == unique_task_id,
                    ContentGenerationTask.user_id == user_id,
                )
            )
            .values(task_status=task_status, task_result=task_result)
        )
        result = await db.execute(stmt)

        return result.rowcount
    

    @staticmethod
    async def view_content_task(
        db: AsyncSession,
        unique_task_id: str,
        user_id: int,
    ):
        stmt = (
            select(ContentGenerationTask.question, ContentGenerationTask.task_status, ContentGenerationTask.task_result)
            .where(
                and_(
                    ContentGenerationTask.unique_task_id == unique_task_id,
                    ContentGenerationTask.user_id == user_id,
                )
            )
        )
        result = await db.execute(stmt)
        return result.one_or_none()


    @staticmethod
    async def delete_content_task(
        db: AsyncSession,
        unique_task_id: str,
        user_id: int,
    ):
        stmt = (
            delete(ContentGenerationTask)
            .where(
                and_(
                    ContentGenerationTask.unique_task_id == unique_task_id,
                    ContentGenerationTask.user_id == user_id,
                )
            )
        )
        result = await db.execute(stmt)

        # if result.rowcount == 0:
        #     raise Exception("Task not found")
        
        return result



    @staticmethod
    async def delete_all_content_task(
        db: AsyncSession,
        user_id: int,
    ):
        stmt = (
            delete(ContentGenerationTask)
            .where(
                ContentGenerationTask.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        
        return result







class ContentTaskRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tasks_page(
        self,
        user_id: int,
        limit: int,
        cursor: Optional[str] = None,
    ) -> tuple[list[ContentGenerationTask], Optional[str]]:

        query = (
            select(ContentGenerationTask)
            .where(ContentGenerationTask.user_id == user_id)
            .order_by(
                ContentGenerationTask.created_at.desc(),
                ContentGenerationTask.id.desc(),
            )
            .limit(limit + 1) 
        )

        if cursor:
            cursor_id, cursor_created_at = decode_cursor(cursor)
        
            query = query.where(
                (ContentGenerationTask.created_at < cursor_created_at)
                | and_(
                    ContentGenerationTask.created_at == cursor_created_at,
                    ContentGenerationTask.id < cursor_id,
                )
            )

        result = await self.db.execute(query)
        rows = result.scalars().all()

       
        has_next = len(rows) > limit
        tasks = list(rows[:limit])

        next_cursor: Optional[str] = None
        if has_next and tasks:
            last = tasks[-1]
            next_cursor = encode_cursor(last.id, last.created_at)

        return tasks, next_cursor