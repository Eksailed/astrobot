from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.chat_message import ChatMessage


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_message(self, user_id: int, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(user_id=user_id, role=role, content=content)
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def get_recent_messages(self, user_id: int, limit: int = 10) -> list[ChatMessage]:
        query = (
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        messages = list(result.scalars().all())
        messages.reverse()  # Return in chronological order
        return messages

    async def clear_history(self, user_id: int) -> None:
        stmt = delete(ChatMessage).where(ChatMessage.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.commit()
