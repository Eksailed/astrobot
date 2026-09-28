from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.user_repo import UserRepository
from db.repositories.subscription_repo import SubscriptionRepository
from services.limits import check_and_increment_limit
from services.tarot.spreads import (
    draw_card_of_the_day,
    draw_three_cards_spread,
    draw_love_spread,
    draw_career_spread,
    DrawnCard,
)
from bot.keyboards.reply import get_pro_promo_keyboard, get_tarot_menu_keyboard

router = Router(name="tarot_handlers")


@router.message(F.text == "🃏 Карта Таро", StateFilter("*"))
@router.message(Command("tarot"), StateFilter("*"))
async def tarot_menu(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start для настройки профиля.")
        return

    sub_repo = SubscriptionRepository(session)
    active_sub = await sub_repo.get_active_subscription(user.id)
    is_pro = active_sub is not None

    if is_pro:
        text = (
            "🃏 **Священное Таро (PRO доступ ⭐️)**\n\n"
            "Вам доступны все виды раскладов без суточных ограничений. "
            "Сфокусируйтесь на волнующем вопросе и выберите расклад:"
        )
    else:
        text = (
            "🃏 **Таро Оракул**\n\n"
            "В бесплатной версии доступен **1 расклад в день** (обновляется в полночь).\n"
            "Выберите интересующий вас расклад:"
        )

    await message.answer(text, reply_markup=get_tarot_menu_keyboard(is_pro), parse_mode="Markdown")


def format_card(drawn: DrawnCard) -> str:
    return (
        f"✨ **{drawn.card.name_ru}** ({drawn.card.name_en})\n"
        f"🔄 {drawn.position_str}\n"
        f"🔑 Энергии: _{', '.join(drawn.card.keywords)}_\n"
        f"📖 {drawn.meaning}"
    )


@router.callback_query(F.data == "tarot_day")
async def on_tarot_day(callback: CallbackQuery, session: AsyncSession) -> None:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Пожалуйста, начните с /start", show_alert=True)
        return

    sub_repo = SubscriptionRepository(session)
    is_pro = (await sub_repo.get_active_subscription(user.id)) is not None

    allowed, count, max_lim = await check_and_increment_limit(user.id, "tarot", is_pro, session=session)
    if not allowed:
        # User already consumed limit, show their fixed daily card
        drawn = draw_card_of_the_day(user_id=user.telegram_id)
        await callback.message.answer(
            f"🃏 **Ваша Карта Дня на сегодня уже вытянута:**\n\n"
            f"{format_card(drawn)}\n\n"
            "⏳ Бесплатный суточный лимит: **1/1** (сброс в полночь по МСК).\n"
            "Оформите **PRO**, чтобы делать неограниченные расклады в любое время!",
            reply_markup=get_pro_promo_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer()
        return

    drawn = draw_card_of_the_day(user_id=user.telegram_id)
    text = (
        f"🃏 **Ваша Карта Дня на сегодня:**\n\n"
        f"{format_card(drawn)}\n\n"
        f"💡 _Совет: Держите этот образ в фокусе внимания сегодня при принятии решений._"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "tarot_three")
async def on_tarot_three(callback: CallbackQuery, session: AsyncSession) -> None:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Пожалуйста, начните с /start", show_alert=True)
        return

    sub_repo = SubscriptionRepository(session)
    is_pro = (await sub_repo.get_active_subscription(user.id)) is not None

    allowed, _, _ = await check_and_increment_limit(user.id, "tarot", is_pro, session=session)
    if not allowed:
        await callback.message.answer(
            "🃏 **Бесплатный суточный лимит раскладов исчерпан (1/1).**\n\n"
            "Вы уже использовали свой бесплатный расклад на сегодня. "
            "Лимит сбрасывается в 00:00 по МСК. Оформите **PRO**, чтобы делать триплеты и тематические расклады без ограничений!",
            reply_markup=get_pro_promo_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer()
        return

    spread = draw_three_cards_spread()
    lines = ["🔮 **Расклад «Прошлое — Настоящее — Будущее»:**\n"]
    for position, drawn in spread:
        lines.append(f"📍 **{position}**\n{format_card(drawn)}\n")

    lines.append("💡 _Свяжите три аркана воедино: прошлое объясняет истоки, настоящее указывает на фокус, будущее показывает вектор._")
    await callback.message.answer("\n".join(lines), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "tarot_love")
async def on_tarot_love(callback: CallbackQuery, session: AsyncSession) -> None:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not user:
        return

    sub_repo = SubscriptionRepository(session)
    is_pro = (await sub_repo.get_active_subscription(user.id)) is not None

    if not is_pro:
        await callback.message.answer(
            "❤️ **Расклад «Любовь и Отношения» входит в подписку PRO.**\n\n"
            "Он подробно раскрывает:\n"
            "• Ваши истинные чувства и подсознательные страхи\n"
            "• Мысли и намерения партнера\n"
            "• Кармический потенциал союза\n\n"
            "Оформите подписку PRO за 150 ⭐️, чтобы открыть этот расклад!",
            reply_markup=get_pro_promo_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer()
        return

    spread = draw_love_spread()
    lines = ["❤️ **Глубокий расклад «Любовь и Отношения»:**\n"]
    for position, drawn in spread:
        lines.append(f"📍 **{position}**\n{format_card(drawn)}\n")

    await callback.message.answer("\n".join(lines), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "tarot_career")
async def on_tarot_career(callback: CallbackQuery, session: AsyncSession) -> None:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not user:
        return

    sub_repo = SubscriptionRepository(session)
    is_pro = (await sub_repo.get_active_subscription(user.id)) is not None

    if not is_pro:
        await callback.message.answer(
            "💼 **Расклад «Карьера и Финансы» входит в подписку PRO.**\n\n"
            "Он анализирует:\n"
            "• Реальное финансовое положение и денежные потоки\n"
            "• Скрытые барьеры и конкурентов\n"
            "• Точный совет арканов для масштабирования дохода\n\n"
            "Оформите подписку PRO за 150 ⭐️, чтобы открыть этот расклад!",
            reply_markup=get_pro_promo_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer()
        return

    spread = draw_career_spread()
    lines = ["💼 **Расклад «Карьера, Бизнес и Деньги»:**\n"]
    for position, drawn in spread:
        lines.append(f"📍 **{position}**\n{format_card(drawn)}\n")

    await callback.message.answer("\n".join(lines), parse_mode="Markdown")
    await callback.answer()
