from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    PreCheckoutQuery,
    LabeledPrice,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.repositories.user_repo import UserRepository
from db.repositories.subscription_repo import SubscriptionRepository
from bot.keyboards.reply import get_pro_invoice_keyboard

router = Router(name="payments_handlers")


PRO_BENEFITS_TEXT = (
    "⭐️ **Преимущества подписки PRO (299 ₽ / ~{stars} Stars в месяц):**\n\n"
    "♾️ **Безлимитный ИИ-астролог** — любые вопросы в любое время без суточных ограничений.\n"
    "🃏 **Неограниченные расклады Таро** — глубокие триплеты и кельтский крест.\n"
    "💞 **Синастрия (совместимость)** — детальный разбор отношений по двум картам.\n"
    "📅 **Прогноз на месяц вперед** — расширенные транзиты медленных планет (Юпитер, Сатурн, Плутон).\n\n"
    "Оплата происходит мгновенно и безопасно через **Telegram Stars**."
)


@router.message(F.text == "⭐ Pro-подписка", StateFilter("*"))
@router.message(Command("pro"), StateFilter("*"))
@router.callback_query(F.data == "buy_pro", StateFilter("*"))
async def send_subscription_invoice(
    event: Message | CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await state.clear()
    message = event if isinstance(event, Message) else event.message
    user_id = event.from_user.id

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(user_id)
    if not user:
        user, _ = await user_repo.get_or_create(user_id, event.from_user.username)

    sub_repo = SubscriptionRepository(session)
    active_sub = await sub_repo.get_active_subscription(user.id)

    if active_sub:
        expires_str = active_sub.expires_at.strftime("%d.%m.%Y")
        await message.answer(
            f"✅ У вас уже активна подписка **PRO** до **{expires_str}**!\n"
            f"Все лимиты сняты. При повторной оплате подписка продлевается на 30 дней.",
            parse_mode="Markdown",
        )

    prices = [LabeledPrice(label="Pro доступ на 30 дней", amount=settings.PRO_PRICE_STARS)]

    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title="🌟 Подписка AstroBot PRO (1 месяц)",
        description=PRO_BENEFITS_TEXT.format(stars=settings.PRO_PRICE_STARS),
        payload=f"pro_sub_{user.id}",
        currency="XTR",  # Telegram Stars
        prices=prices,
        reply_markup=get_pro_invoice_keyboard(settings.PRO_PRICE_STARS),
    )

    if isinstance(event, CallbackQuery):
        await event.answer()


@router.pre_checkout_query()
async def process_pre_checkout_query(query: PreCheckoutQuery) -> None:
    """Approve checkout instantly for Stars"""
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, session: AsyncSession) -> None:
    payment = message.successful_payment
    charge_id = payment.telegram_payment_charge_id

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        user, _ = await user_repo.get_or_create(message.from_user.id, message.from_user.username)

    sub_repo = SubscriptionRepository(session)
    sub = await sub_repo.add_or_extend_subscription(
        user_id=user.id,
        days=30,
        plan="pro",
        telegram_charge_id=charge_id,
    )

    expires_str = sub.expires_at.strftime("%d.%m.%Y")
    await message.answer(
        f"🎉 **Поздравляем! Ваша подписка PRO активирована!**\n\n"
        f"📅 Срок действия: до **{expires_str}**.\n\n"
        f"Все лимиты на ИИ-чат и расклады Таро сняты. Наслаждайтесь персональной астрологией нового поколения!",
        parse_mode="Markdown",
    )
