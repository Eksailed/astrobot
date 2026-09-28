from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.subscription import Subscription


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_subscription(self, user_id: int) -> Subscription | None:
        now = datetime.utcnow()
        query = (
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.is_active.is_(True),
                Subscription.expires_at > now,
            )
            .order_by(Subscription.expires_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def add_or_extend_subscription(
        self,
        user_id: int,
        days: int = 30,
        plan: str = "pro",
        telegram_charge_id: str | None = None,
    ) -> Subscription:
        now = datetime.utcnow()
        current_sub = await self.get_active_subscription(user_id)

        if current_sub:
            # Extend existing active subscription
            start_date = current_sub.expires_at
            current_sub.expires_at = start_date + timedelta(days=days)
            current_sub.telegram_charge_id = telegram_charge_id or current_sub.telegram_charge_id
            await self.session.commit()
            await self.session.refresh(current_sub)
            return current_sub
        else:
            # Create new subscription
            expires = now + timedelta(days=days)
            new_sub = Subscription(
                user_id=user_id,
                plan=plan,
                starts_at=now,
                expires_at=expires,
                telegram_charge_id=telegram_charge_id,
                is_active=True,
            )
            self.session.add(new_sub)
            await self.session.commit()
            await self.session.refresh(new_sub)
            return new_sub
