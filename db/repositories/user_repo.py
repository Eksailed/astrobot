from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        language_code: str = "ru",
    ) -> tuple[User, bool]:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language_code=language_code,
            is_agreed_terms=False,
        )
        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user, True
        except Exception:
            await self.session.rollback()
            existing = await self.get_by_telegram_id(telegram_id)
            if existing:
                return existing, False
            raise

    async def set_agreed_terms(self, user_id: int) -> None:
        user = await self.session.get(User, user_id)
        if user:
            user.is_agreed_terms = True
            await self.session.commit()

    async def delete_user_data(self, telegram_id: int) -> bool:
        """Completely delete user and all associated data (/delete command for GDPR/compliance)"""
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return False
        await self.session.delete(user)
        await self.session.commit()
        return True
