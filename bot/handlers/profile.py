import re
from datetime import datetime, time
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.profile import ProfileSetup
from bot.keyboards.reply import get_skip_time_keyboard, get_main_menu_keyboard
from db.repositories.user_repo import UserRepository
from db.repositories.chart_repo import ChartRepository
from services.astrology.geocoding import resolve_location
from services.astrology.ephemeris import calculate_chart

router = Router(name="profile_handlers")


@router.message(ProfileSetup.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    try:
        birth_date = datetime.strptime(text, "%d.%m.%Y").date()
        if birth_date.year < 1920 or birth_date.year > datetime.utcnow().year:
            raise ValueError()
    except Exception:
        await message.answer("⚠️ Неверный формат даты. Пожалуйста, введите дату в виде `ДД.ММ.ГГГГ` (например: `24.08.1998`):", parse_mode="Markdown")
        return

    await state.update_data(birth_date=birth_date.isoformat())
    await message.answer(
        "Шаг 2 из 3: Введите **время рождения** в формате `ЧЧ:ММ` (например: `14:30`).\n\n"
        "Точное время необходимо для расчета Асцендента и астрологических домов. "
        "Если не знаете, нажмите кнопку ниже:",
        reply_markup=get_skip_time_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(ProfileSetup.waiting_for_birth_time)


@router.message(ProfileSetup.waiting_for_birth_time)
async def process_birth_time(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    birth_time = None

    if "Не знаю" not in text:
        try:
            parsed = datetime.strptime(text, "%H:%M").time()
            birth_time = parsed
        except Exception:
            await message.answer(
                "⚠️ Неверный формат времени. Введите время как `ЧЧ:ММ` (например, `08:45`) или нажмите кнопку «Не знаю точное время»:",
                reply_markup=get_skip_time_keyboard(),
                parse_mode="Markdown",
            )
            return

    await state.update_data(birth_time=birth_time.strftime("%H:%M") if birth_time else None)
    await message.answer(
        "Шаг 3 из 3: Введите **город (место) вашего рождения** (например: `Москва`, `Алматы`, `Санкт-Петербург`):",
        parse_mode="Markdown",
    )
    await state.set_state(ProfileSetup.waiting_for_birth_place)


@router.message(ProfileSetup.waiting_for_birth_place)
async def process_birth_place(message: Message, state: FSMContext, session: AsyncSession) -> None:
    city_query = message.text.strip()
    status_msg = await message.answer("✨ Идет расчет швейцарских эфемерид и планетарных положений...")

    try:
        data = await state.get_data()
        birth_date = datetime.fromisoformat(data["birth_date"]).date()
        birth_time_str = data.get("birth_time")
        birth_time = datetime.strptime(birth_time_str, "%H:%M").time() if birth_time_str else None

        # Resolve Geocoding & Timezone
        loc = await resolve_location(city_query)

        # Calculate full chart
        chart_data = calculate_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            latitude=loc.latitude,
            longitude=loc.longitude,
            timezone_str=loc.timezone_str,
        )

        # Save to Database
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            user, _ = await user_repo.get_or_create(message.from_user.id, message.from_user.username)

        chart_repo = ChartRepository(session)
        chart = await chart_repo.save_or_update(
            user_id=user.id,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=loc.place_name,
            latitude=loc.latitude,
            longitude=loc.longitude,
            timezone_str=loc.timezone_str,
            sun_sign=chart_data["sun_sign"],
            moon_sign=chart_data["moon_sign"],
            ascendant=chart_data["ascendant_sign"],
            chart_data=chart_data,
        )

        await state.clear()

        planets = chart_data.get("planets", {})
        sun = planets.get("Sun", {})
        moon = planets.get("Moon", {})
        asc = chart_data.get("ascendant") or {}

        asc_sign = asc.get("sign_ru", "Не определен")
        asc_deg_str = f"({asc.get('degree_in_sign')}°)" if asc.get("degree_in_sign") is not None else ""

        chart_text = (
            f"🌌 **Ваша Натальная Карта успешно рассчитана!**\n\n"
            f"📍 **Место:** {loc.place_name} ({loc.timezone_str})\n"
            f"📅 **Дата:** {birth_date.strftime('%d.%m.%Y')} {birth_time_str or '(время 12:00)'}\n\n"
            f"☀️ **Солнце в знаке:** {sun.get('sign_ru')} {sun.get('symbol')} ({sun.get('degree_in_sign')}°)\n"
            f"🌙 **Луна в знаке:** {moon.get('sign_ru')} {moon.get('symbol')} ({moon.get('degree_in_sign')}°)\n"
            f"🏹 **Асцендент (ASC):** {asc_sign} {asc_deg_str}\n\n"
            f"✨ Теперь вам доступны персональные транзитные прогнозы дня, карта Таро и диалог с персональным ИИ-астрологом!"
        )

        await status_msg.delete()
        await message.answer(chart_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    except Exception as e:
        await status_msg.delete()
        await message.answer(f"⚠️ Произошла ошибка при расчете: {e}. Пожалуйста, попробуйте снова, отправив /start.")


@router.message(F.text == "🌟 Моя натальная карта", StateFilter("*"))
async def show_natal_chart(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start для настройки профиля.")
        return

    chart_repo = ChartRepository(session)
    chart = await chart_repo.get_by_user_id(user.id)
    if not chart:
        await message.answer("Ваша натальная карта еще не заполнена. Отправьте /start чтобы ввести данные.")
        return

    planets = chart.chart_data.get("planets", {})
    planets_text = "\n".join([
        f"• {p['name_ru']}: {p['sign_ru']} {p.get('symbol', '')} ({p['degree_in_sign']}°){' ℞' if p.get('is_retrograde') else ''}"
        for p in planets.values()
    ])

    text = (
        f"📜 **Ваш Астрологический Паспорт**\n\n"
        f"📍 Рождение: {chart.birth_place}\n"
        f"🕒 {chart.birth_date.strftime('%d.%m.%Y')} {chart.birth_time.strftime('%H:%M') if chart.birth_time else '12:00'}\n\n"
        f"**Планетарные позиции:**\n"
        f"{planets_text}\n\n"
        f"Асцендент: **{chart.ascendant}**\n\n"
        f"💡 Чтобы задать вопрос о любом аспекте или планете в карте, нажмите «💬 Чат с Астрологом»."
    )
    await message.answer(text, parse_mode="Markdown")
