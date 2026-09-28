import logging
import httpx
from core.config import settings

logger = logging.getLogger(__name__)


async def generate_ai_response(
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> str:
    """
    Calls OpenRouter API with Qwen 2.5 72B (or configured model).
    """
    if not settings.OPENROUTER_API_KEY:
        return (
            "✨ Звезды шепчут: API-ключ ИИ-астролога пока не настроен администратором. "
            "Пожалуйста, добавьте OPENROUTER_API_KEY в файл .env."
        )

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me/AstroPersonalBot",
        "X-Title": "AstroBot AI Astrologer",
    }

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        logger.error(f"OpenRouter HTTP error: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 402:
            return (
                "✨ **Сообщение от ИИ-оракула:**\n\n"
                "Ключ OpenRouter успешно подключен, но на балансе аккаунта сейчас 0$ (недостаточно кредитов для вызова Qwen 2.5 72B).\n\n"
                "Пополните баланс на [openrouter.ai/settings/credits](https://openrouter.ai/settings/credits) (даже $3-5 хватит на тысячи консультаций)!"
            )
        elif e.response.status_code == 429:
            return "🌌 Оракул перегружен запросами в данный момент. Попробуйте еще раз через пару минут."
        return "🌌 Связь с небесными сферами временно затруднена. Пожалуйста, попробуйте задать вопрос через минуту."
    except Exception as e:
        logger.error(f"Error querying OpenRouter: {e}")
        return "🌌 Произошла ошибка при обращении к оракулу. Попробуйте еще раз чуть позже."
