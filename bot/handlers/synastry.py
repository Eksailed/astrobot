from datetime import datetime, time
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.user_repo import UserRepository
from db.repositories.chart_repo import ChartRepository
from db.repositories.subscription_repo import SubscriptionRepository
from services.astrology.geocoding import resolve_location
from services.astrology.ephemeris import calculate_chart
from services.astrology.synastry import calculate_synastry
from bot.states.synastry import SynastrySetup
from bot.keyboards.reply import (
    get_synastry_choice_keyboard,
    get_skip_time_keyboard,
    get_main_menu_keyboard,
    get_pro_promo_keyboard,
)

router = Router(name="synastry_handlers")


def make_progress_bar(percentage: int) -> str:
    filled = round(percentage / 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"`[{bar}]` {percentage}%"


@router.message(F.text == "💞 Совместимость", StateFilter("*"))
@router.message(Command("synastry"), StateFilter("*"))
async def synastry_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала введите данные рождения через /start.")
        return

    chart_repo = ChartRepository(session)
    chart = await chart_repo.get_by_user_id(user.id)
    if not chart:
        await message.answer("Для расчета совместимости сначала рассчитайте вашу натальную карту через /start.")
        return

    bot_user = await message.bot.get_me()
    text = (
        "💞 **Астрологическая совместимость (Синастрия)**\n\n"
        "Синастрия — это наложение двух натальных карт. Она показывает истинную химию, "
        "эмоциональное притяжение, возможные камни преткновения и кармические связи в паре.\n\n"
        "Как вы хотите проверить совместимость?"
    )
    await message.answer(
        text,
        reply_markup=get_synastry_choice_keyboard(bot_user.username, user.id),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "synastry_manual")
async def on_synastry_manual(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(
        "✍️ **Шаг 1 из 3:** Введите **дату рождения партнера** в формате `ДД.ММ.ГГГГ` (например: `18.11.1996`):",
        parse_mode="Markdown",
    )
    await state.set_state(SynastrySetup.waiting_for_partner_date)
    await callback.answer()


@router.message(SynastrySetup.waiting_for_partner_date)
async def process_partner_date(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    try:
        partner_date = datetime.strptime(text, "%d.%m.%Y").date()
        if partner_date.year < 1920 or partner_date.year > datetime.utcnow().year:
            raise ValueError()
    except Exception:
        await message.answer(
            "⚠️ Неверный формат даты. Введите дату как `ДД.ММ.ГГГГ` (например: `18.11.1996`):",
            parse_mode="Markdown",
        )
        return

    await state.update_data(partner_date=partner_date.isoformat())
    await message.answer(
        "**Шаг 2 из 3:** Введите **время рождения партнера** в формате `ЧЧ:ММ` (например: `15:40`) или нажмите кнопку пропуска:",
        reply_markup=get_skip_time_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(SynastrySetup.waiting_for_partner_time)


@router.message(SynastrySetup.waiting_for_partner_time)
async def process_partner_time(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    partner_time = None
    if "Не знаю" not in text:
        try:
            partner_time = datetime.strptime(text, "%H:%M").time()
        except Exception:
            await message.answer(
                "⚠️ Неверный формат. Введите время как `ЧЧ:ММ` или нажмите «Не знаю точное время»:",
                reply_markup=get_skip_time_keyboard(),
                parse_mode="Markdown",
            )
            return

    await state.update_data(partner_time=partner_time.strftime("%H:%M") if partner_time else None)
    await message.answer(
        "**Шаг 3 из 3:** Введите **город рождения партнера** (например: `Москва`, `Казань`):",
        parse_mode="Markdown",
    )
    await state.set_state(SynastrySetup.waiting_for_partner_place)


@router.message(SynastrySetup.waiting_for_partner_place)
async def process_partner_place(message: Message, state: FSMContext, session: AsyncSession) -> None:
    city_query = message.text.strip()
    status_msg = await message.answer("✨ Идет наложение двух космограмм и расчет синастрии...")

    try:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        chart_repo = ChartRepository(session)
        user_chart = await chart_repo.get_by_user_id(user.id)

        data = await state.get_data()
        partner_date = datetime.fromisoformat(data["partner_date"]).date()
        partner_time_str = data.get("partner_time")
        partner_time = datetime.strptime(partner_time_str, "%H:%M").time() if partner_time_str else None

        # Geocode partner city
        partner_loc = await resolve_location(city_query)

        # Calculate partner chart
        partner_chart_data = calculate_chart(
            birth_date=partner_date,
            birth_time=partner_time,
            latitude=partner_loc.latitude,
            longitude=partner_loc.longitude,
            timezone_str=partner_loc.timezone_str,
        )

        # Calculate synastry
        syn_result = calculate_synastry(user_chart.chart_data, partner_chart_data)

        sub_repo = SubscriptionRepository(session)
        is_pro = (await sub_repo.get_active_subscription(user.id)) is not None

        await state.clear()
        await status_msg.delete()

        # Build response message
        lines = [
            f"💞 **Астрологическая совместимость пары**\n",
            f"👤 **Вы:** {user_chart.sun_sign} (ASC {user_chart.ascendant or '—'})",
            f"👤 **Партнер:** {partner_chart_data['sun_sign']} (ASC {partner_chart_data['ascendant_sign'] or '—'})\n",
            f"✨ **Общий индекс гармонии:** {make_progress_bar(syn_result['overall_percentage'])}\n",
            f"**Оценки по ключевым сферам:**",
            f"❤️ Любовь и влечение: {make_progress_bar(syn_result['love_score'])}",
            f"🌙 Душевный комфорт: {make_progress_bar(syn_result['emotional_score'])}",
            f"💡 Общение и темы: {make_progress_bar(syn_result['intellect_score'])}",
            f"🪐 Надежность союза: {make_progress_bar(syn_result['stability_score'])}\n",
            f"🟢 **Ключевые точки притяжения:**",
        ]

        for h in syn_result["highlights"]:
            lines.append(f"• {h}")

        lines.append(f"\n🟡 **Зоны внимания (точки роста):**")
        for c in syn_result["challenges"]:
            lines.append(f"• {c}")

        if not is_pro:
            lines.append(
                f"\n⭐️ _В подписке PRO доступен подробный поминутный разбор всех {syn_result['inter_aspects_count']} межпланетарных аспектов пары и психологический анализ кармических узлов!_"
            )
            await message.answer(
                "\n".join(lines),
                reply_markup=get_pro_promo_keyboard(),
                parse_mode="Markdown",
            )
        else:
            lines.append("\n🌟 **PRO-анализ:** У вас сильная синастрическая связь. Используйте точки притяжения для вдохновения и поддерживайте открытый диалог.")
            await message.answer(
                "\n".join(lines),
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown",
            )
    except Exception as e:
        await status_msg.delete()
        await message.answer(f"⚠️ Ошибка при расчете синастрии: {e}. Попробуйте снова через меню.", reply_markup=get_main_menu_keyboard())
