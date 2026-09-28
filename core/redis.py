from redis.asyncio import Redis, from_url
from core.config import settings

redis_client: Redis | None = None


async def init_redis() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def get_redis() -> Redis:
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized")
    return redis_client
