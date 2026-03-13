from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, delete
from app.models.sql_models import UserSocialAccounts



class BlueskyRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_bluesky_account(
        self,
        user_id: int,
        social_platform: str,
        handle: str,
        app_password: str
    ):

        result = await self.db.execute(
            select(UserSocialAccounts).where(
                UserSocialAccounts.user_id == user_id,
                UserSocialAccounts.social_platform == social_platform,
            )
        )

        existing = result.scalar_one_or_none()

        if existing:
            existing.handle = handle
            existing.app_password = app_password
            return existing

        new_account = UserSocialAccounts(
            user_id=user_id,
            social_platform=social_platform,
            handle=handle,
            app_password=app_password,
        )

        self.db.add(new_account)

        await self.db.flush()   

        return new_account
    


    async def get_bluesky_account(self, user_id: int):
        result = await self.db.execute(
            select(UserSocialAccounts.app_password, UserSocialAccounts.handle).where(
                UserSocialAccounts.user_id == user_id,
                UserSocialAccounts.social_platform == "bluesky",
            )
        )

        return result.one_or_none()
    

    # async def get_bluesky_account(self, user_id: int):
    #     result = await self.db.execute(
    #         select(UserSocialAccounts).where(
    #             UserSocialAccounts.user_id == user_id,
    #             UserSocialAccounts.social_platform == "bluesky",
    #         )
    #     )
    #     return result.scalar_one_or_none()

    async def delete_account(self, account: UserSocialAccounts):
        await self.db.delete(account)