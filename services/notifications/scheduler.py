import asyncio
import logging
from datetime import datetime, time
from aiogram import Bot
from sqlalchemy import select
from db.session import async_session_factory
from db.models.user import User
from db.models.natal_chart import NatalChart
from services.astrology.chart_calculator import get_current_transits
from services.tarot.spreads import draw_card_of_the_day

logger = logging.getLogger("astro_scheduler")


async def send_morning_horoscopes(bot: Bot) -> None:
    """
    Sends personalized daily morning forecast to active users.
    """
    logger.info("Running daily morning horoscope delivery...")
    async with async_session_factory() as session:
        # Fetch users with charts
        query = (
            select(User, NatalChart)
            .join(NatalChart, User.id == NatalChart.user_id)
            .where(User.is_agreed_terms.is_(True))
        )
        result = await session.execute(query)
        rows = result.all()

        for user, chart in rows:
            try:
                transits = get_current_transits(chart.chart_data)
                transit_text = (
                    f"Сегодня активен аспект: {transits[0]['transit_planet']} {transits[0]['aspect']} {transits[0]['natal_planet']} ✨"
                    if transits
                    else "Сегодня спокойная космическая погода для вашего знака 🌿"
                )
                daily_card = draw_card_of_the_day(user_id=user.id)

                message_text = (
                    f"☀️ **Доброе утро, {user.first_name or 'натив'}!**\n\n"
                    f"🌌 {transit_text}\n"
                    f"🃏 Ваша Карта Дня: **{daily_card.card.name_ru}** ({daily_card.position_str})\n\n"
                    f"Желаем гармоничного и продуктивного дня! "
                    f"Нажмите «🔮 Гороскоп дня» в меню для подробного прогноза."
                )
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message_text,
                    parse_mode="Markdown",
                )
                await asyncio.sleep(0.05)  # Rate limiting protection
            except Exception as e:
                logger.warning(f"Failed to send morning horoscope to user {user.telegram_id}: {e}")


async def morning_scheduler_loop(bot: Bot, target_hour_msk: int = 9) -> None:
    """
    Checks time every 60 seconds and triggers morning broadcast once a day.
    """
    already_sent_today = False
    while True:
        try:
            # MSK is UTC+3
            now_utc = datetime.utcnow()
            hour_msk = (now_utc.hour + 3) % 24

            if hour_msk == target_hour_msk and not already_sent_today:
                await send_morning_horoscopes(bot)
                already_sent_today = True

            # Reset sent flag after hour passes
            if hour_msk != target_hour_msk:
                already_sent_today = False

            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in morning scheduler loop: {e}")
            await asyncio.sleep(60)
