from sqlalchemy.ext.asyncio import AsyncSession
from app.services.content_gen_service import ContentGenerationService

async def save_database(
        db: AsyncSession,
        task_status: str,
        task_result: str,
        unique_task_id: str,
        user_id: int,):
    return await ContentGenerationService.update_content_task(db, task_status, task_result, unique_task_id, user_id)
    