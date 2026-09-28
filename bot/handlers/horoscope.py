from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.user_repo import UserRepository
from db.repositories.chart_repo import ChartRepository
from services.astrology.chart_calculator import get_current_transits

router = Router(name="horoscope_handlers")


@router.message(F.text == "🔮 Гороскоп дня", StateFilter("*"))
@router.message(Command("horoscope"), StateFilter("*"))
async def daily_horoscope(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала заполните профиль через /start.")
        return

    chart_repo = ChartRepository(session)
    chart = await chart_repo.get_by_user_id(user.id)
    if not chart:
        await message.answer("Для расчета персонального гороскопа необходимо рассчитать натальную карту. Отправьте /start.")
        return

    # Calculate live transits to natal chart
    transits = get_current_transits(chart.chart_data)

    today_str = datetime.utcnow().strftime("%d.%m.%Y")

    if not transits:
        transit_desc = "✨ Сегодня на небе спокойная космическая погода для вашей натальной карты. Отличный день для рутинных дел, внутренней гармонии и восстановления ресурса."
    else:
        aspect_lines = []
        for t in transits[:5]:
            aspect_lines.append(f"• **Транзитная {t['transit_planet']} {t['aspect']} натальное {t['natal_planet']}** ({'гармоничный аспект 🟢' if t['nature'] == 'harmonious' else 'аспект напряжения/динамики 🟡'})")
        transit_desc = "\n".join(aspect_lines)

    horoscope_text = (
        f"🔮 **Персональный астрологический прогноз на {today_str}**\n"
        f"Для натива: **{chart.sun_sign}** (ASC {chart.ascendant or '—'})\n\n"
        f"🌌 **Активные транзитные влияния сегодня:**\n"
        f"{transit_desc}\n\n"
        f"💡 **Рекомендация дня:**\n"
        f"Обратите внимание на сферы общения и личной продуктивности. Не форсируйте события там, где чувствуете внутреннее сопротивление. "
        f"Используйте энергию планет для созидания!\n\n"
        f"💬 _Хотите узнать подробнее о влиянии сегодняшних транзитов на карьеру или отношения? Нажмите «💬 Чат с Астрологом»._"
    )

    await message.answer(horoscope_text, parse_mode="Markdown")
