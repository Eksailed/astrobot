from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.user_repo import UserRepository
from db.repositories.chart_repo import ChartRepository
from db.repositories.subscription_repo import SubscriptionRepository
from services.astrology.chart_calculator import get_current_transits
from services.astrology.monthly_forecast import calculate_monthly_forecast
from bot.keyboards.reply import get_pro_promo_keyboard

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
        f"📅 _Хотите заглянуть вперед? Отправьте команду /month для прогноза на месяц._"
    )

    await message.answer(horoscope_text, parse_mode="Markdown")


@router.message(Command("month"), StateFilter("*"))
async def monthly_horoscope(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала заполните профиль через /start.")
        return

    chart_repo = ChartRepository(session)
    chart = await chart_repo.get_by_user_id(user.id)
    if not chart:
        await message.answer("Сначала введите данные рождения через /start.")
        return

    sub_repo = SubscriptionRepository(session)
    is_pro = (await sub_repo.get_active_subscription(user.id)) is not None

    forecast = calculate_monthly_forecast(chart.chart_data)

    if not is_pro:
        text = (
            f"📅 **Астрологический прогноз на месяц ({forecast['month_name']})**\n"
            f"Для натива: **{chart.sun_sign}**\n\n"
            f"✨ **Ключевой фокус месяца:**\n"
            f"{forecast['key_themes'][0]}\n\n"
            f"⭐️ **Полный прогноз на 30 дней доступен в PRO:**\n"
            f"• Календарь Дней Силы (точки максимальной удачи)\n"
            f"• Дни осторожности (риски конфликтов и импульсивных трат)\n"
            f"• Транзиты медленных планет (Марс, Юпитер, Сатурн, Плутон)\n"
            f"• Детальные разборы сфер карьеры, отношений и здоровья\n\n"
            f"Оформите подписку PRO за 150 ⭐️, чтобы открыть прогноз на месяц!"
        )
        await message.answer(text, reply_markup=get_pro_promo_keyboard(), parse_mode="Markdown")
        return

    # Full PRO Response
    lines = [
        f"📅 **Большой персональный прогноз на месяц (PRO ⭐️)**\n",
        f"Для натива: **{chart.sun_sign}** (ASC {chart.ascendant or '—'})\n",
        f"🌟 **Главные темы предстоящих 30 дней:**",
    ]
    for theme in forecast["key_themes"]:
        lines.append(f"• {theme}")

    if forecast["power_days"]:
        lines.append("\n🟢 **Дни Силы (максимальная продуктивность и удача):**")
        for date_str, desc in forecast["power_days"]:
            lines.append(f"• **{date_str}** — {desc}")

    if forecast["caution_days"]:
        lines.append("\n🟡 **Дни Осторожности (внимание и фокус):**")
        for date_str, desc in forecast["caution_days"]:
            lines.append(f"• **{date_str}** — {desc}")

    if forecast["major_transits"]:
        lines.append("\n🪐 **Ключевые транзитные влияния:**")
        for tr in forecast["major_transits"]:
            lines.append(f"• {tr}")

    lines.append("\n💡 _Совет: планируйте ключевые встречи, сделки и старты проектов на Дни Силы._")

    await message.answer("\n".join(lines), parse_mode="Markdown")
