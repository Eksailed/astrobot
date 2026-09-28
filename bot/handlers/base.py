from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.user_repo import UserRepository
from db.repositories.chart_repo import ChartRepository
from bot.states.profile import ProfileSetup
from bot.keyboards.reply import get_consent_keyboard, get_main_menu_keyboard

router = Router(name="base_handlers")

DISCLAIMER_TEXT = (
    "✨ **Добро пожаловать в персональный AI-Астролог!**\n\n"
    "Здесь вы получите расчет персональной натальной карты по точным швейцарским эфемеридам, "
    "ежедневные прогнозы по вашим транзитам, расклады Таро и общение с искусственным интеллектом-астрологом.\n\n"
    "⚠️ **Юридический дисклеймер:**\n"
    "«Развлекательный сервис 18+. Астрология и Таро не являются научным методом. "
    "Не принимайте важных финансовых и медицинских решений на основе прогнозов сервиса».\n\n"
    "Для продолжения подтвердите, что вам исполнилось 18 лет и вы согласны с условиями."
)


@router.message(CommandStart(), StateFilter("*"))
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        language_code=message.from_user.language_code or "ru",
    )

    if not user.is_agreed_terms:
        await message.answer(DISCLAIMER_TEXT, reply_markup=get_consent_keyboard(), parse_mode="Markdown")
        await state.set_state(ProfileSetup.waiting_for_consent)
        return

    chart_repo = ChartRepository(session)
    chart = await chart_repo.get_by_user_id(user.id)

    if not chart:
        await message.answer(
            f"👋 Рады видеть вас, {message.from_user.first_name}!\n\n"
            "Чтобы составить вашу натальную карту, введите вашу **дату рождения** в формате `ДД.ММ.ГГГГ` (например: `15.05.1995`):",
            parse_mode="Markdown",
        )
        await state.set_state(ProfileSetup.waiting_for_birth_date)
    else:
        await message.answer(
            f"🌟 С возвращением, {message.from_user.first_name}!\n\n"
            f"Ваш знак: **{chart.sun_sign}**, Луна в **{chart.moon_sign}**, Асцендент в **{chart.ascendant or 'не указан'}**.\n\n"
            "Выберите раздел в меню снизу:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )


@router.callback_query(F.data == "consent_accept")
async def on_consent_accepted(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if user:
        await user_repo.set_agreed_terms(user.id)

    await callback.message.edit_text(
        "✅ Согласие принято!\n\n"
        "Шаг 1 из 3: Введите вашу **дату рождения** в формате `ДД.ММ.ГГГГ` (например: `15.05.1995`):",
        parse_mode="Markdown",
    )
    await state.set_state(ProfileSetup.waiting_for_birth_date)
    await callback.answer()


@router.message(Command("delete"), StateFilter("*"))
async def cmd_delete(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """GDPR-compliant personal data removal"""
    await state.clear()
    user_repo = UserRepository(session)
    deleted = await user_repo.delete_user_data(message.from_user.id)
    if deleted:
        await message.answer(
            "🗑 Все ваши персональные данные, расчеты натальной карты и история диалогов полностью удалены из системы.\n\n"
            "Если захотите вернуться, просто отправьте команду /start."
        )
    else:
        await message.answer("Ваших данных не найдено в базе.")


@router.message(Command("help"), StateFilter("*"))
async def cmd_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🔮 **Помощь по командам:**\n\n"
        "• `/start` — Главное меню и ваш профиль\n"
        "• `/horoscope` — Гороскоп дня по транзитам\n"
        "• `/tarot` — Карта дня Таро\n"
        "• `/pro` — Оформить подписку Pro (Telegram Stars)\n"
        "• `/delete` — Полное удаление ваших данных\n"
        "• `/help` — Эта справка",
        parse_mode="Markdown",
    )
