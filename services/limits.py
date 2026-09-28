from datetime import date, datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.redis import redis_client
from core.config import settings
from db.models.daily_limit import DailyLimit


# In-memory fallback dictionary: (user_id, action, date_str) -> count
_MEM_LIMITS: dict[tuple[int, str, str], int] = {}


async def check_and_increment_limit(
    user_id: int,
    action: str,  # 'tarot' or 'ai'
    is_pro: bool,
    session: AsyncSession | None = None,
) -> tuple[bool, int, int]:
    """
    Returns (is_allowed, current_count, max_limit).
    Uses Redis if available, otherwise falls back to PostgreSQL/SQLite DB and in-memory cache.
    If user has Pro subscription, unlimited is allowed.
    """
    if is_pro:
        return True, 0, 999999

    max_limit = (
        settings.FREE_DAILY_TAROT
        if action == "tarot"
        else settings.FREE_DAILY_AI_QUESTIONS
    )

    today = date.today()
    today_str = today.isoformat()

    # 1. Try Redis first
    if redis_client is not None:
        try:
            key = f"limit:{user_id}:{action}:{today_str}"
            count = await redis_client.incr(key)
            if count == 1:
                now = datetime.utcnow()
                tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                ttl = int((tomorrow - now).total_seconds())
                await redis_client.expire(key, max(ttl, 60))

            if count > max_limit:
                return False, count, max_limit
            return True, count, max_limit
        except Exception:
            pass  # Fallback to DB

    # 2. Database persistent fallback
    if session is not None:
        try:
            query = select(DailyLimit).where(
                DailyLimit.user_id == user_id,
                DailyLimit.day == today,
            )
            result = await session.execute(query)
            limit_row = result.scalar_one_or_none()

            if limit_row is None:
                limit_row = DailyLimit(
                    user_id=user_id,
                    day=today,
                    tarot_count=0,
                    ai_questions_count=0,
                )
                session.add(limit_row)

            current = limit_row.tarot_count if action == "tarot" else limit_row.ai_questions_count

            if current >= max_limit:
                return False, current + 1, max_limit

            # Increment count
            if action == "tarot":
                limit_row.tarot_count += 1
            else:
                limit_row.ai_questions_count += 1

            await session.commit()
            return True, current + 1, max_limit
        except Exception:
            await session.rollback()

    # 3. In-memory dictionary fallback
    mem_key = (user_id, action, today_str)
    current_mem = _MEM_LIMITS.get(mem_key, 0)
    if current_mem >= max_limit:
        return False, current_mem + 1, max_limit

    _MEM_LIMITS[mem_key] = current_mem + 1
    return True, current_mem + 1, max_limit
