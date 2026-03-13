from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.bluesky_repo import BlueskyRepository
from app.core.security import encrypt_password











class BlueskyServices:

    def __init__(self, db: AsyncSession):
        self.repo = BlueskyRepository(db)
        self.db = db

    async def fetch_bluesky_account(
        self,
        user_id: int,
        social_platform: str,
        handle: str,
        app_password: str
    ):

        account = await self.repo.fetch_bluesky_account(
            user_id,
            social_platform,
            handle,
            app_password = encrypt_password(app_password)
        )
        if not account:
            raise 
        
        await self.db.commit()
        # await self.db.refresh(account)

        return account
    

    async def prepare_bluesky_post(self, user_id: int):

        account = await self.repo.get_bluesky_account(user_id)

        if not account:
            raise BlueskyAccountNotConnected()

        return account
    

    async def disconnect_bluesky(self, user_id: int):

        account = await self.repo.get_bluesky_account(user_id)

        if not account:
            raise BlueskyAccountNotConnected()

        await self.repo.delete_account(account)

        await self.db.commit()

        return {"message": "Bluesky account disconnected."}


class BlueskyAccountNotConnected(Exception):
    pass