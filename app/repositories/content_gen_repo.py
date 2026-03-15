from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql_models import ContentGenerationTask
from sqlalchemy import select, or_, and_, update, delete
from datetime import datetime
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





    @staticmethod
    async def list_content_task(
        db: AsyncSession,
        user_id: int,
        # completed: bool | None,
        limit: int,
        cursor: datetime | None,
        cursor_id: int | None,
    ):
        
        stmt = select(ContentGenerationTask).where(ContentGenerationTask.user_id == user_id)
        
        if cursor and cursor_id:
            cursor_naive = cursor.replace(tzinfo=None)

            stmt = stmt.where(
                or_(
                    ContentGenerationTask.created_at < cursor_naive,
                    and_(
                        ContentGenerationTask.created_at == cursor_naive,
                        ContentGenerationTask.id < cursor_id,
                    ),
                )
            )

        stmt = (
            stmt.order_by(ContentGenerationTask.created_at.desc(), ContentGenerationTask.id.desc()).limit(limit + 1))
        
        result = await db.execute(stmt)

        tasks = result.scalars().all()

        has_next = len(tasks) > limit
        items = tasks[:limit]

        next_cursor = None
        if has_next:
            last = items[-1]
            next_cursor = {
                "cursor": last.created_at,
                "cursor_id": last.id
            }

        return {
            "items": items,
            "next_cursor": next_cursor,
            "has_next": has_next
        }


 