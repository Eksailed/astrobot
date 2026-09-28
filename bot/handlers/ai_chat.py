from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.user_repo import UserRepository
from db.repositories.chart_repo import ChartRepository
from db.repositories.subscription_repo import SubscriptionRepository
from db.repositories.chat_repo import ChatRepository
from services.limits import check_and_increment_limit
from services.ai.prompts import build_system_prompt
from services.ai.openrouter import generate_ai_response
from services.astrology.chart_calculator import get_current_transits
from bot.states.profile import AIChatState
from bot.keyboards.reply import get_pro_promo_keyboard, get_main_menu_keyboard

router = Router(name="ai_chat_handlers")


@router.message(F.text == "💬 Чат с Астрологом", StateFilter("*"))
async def start_ai_chat(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала введите данные рождения через /start.")
        return

    sub_repo = SubscriptionRepository(session)
    is_pro = (await sub_repo.get_active_subscription(user.id)) is not None

    status_text = "⭐️ У вас **Pro-доступ**: безлимитные вопросы!" if is_pro else "💡 В бесплатной версии доступен **1 вопрос в день** (Pro снимает лимит)."

    await message.answer(
        f"🌌 **Диалог с персональным ИИ-астрологом**\n\n"
        f"{status_text}\n\n"
        "Я помню вашу натальную карту и текущие транзиты. Спросите меня о:\n"
        "• Совместимости и отношениях\n"
        "• Карьерных перспективах и талантах\n"
        "• Причинах текущего настроения или упадка сил\n\n"
        "Напишите ваш вопрос следующим сообщением (или напишите `Выход` для возврата в меню):",
        parse_mode="Markdown",
    )
    await state.set_state(AIChatState.in_dialog)


@router.message(AIChatState.in_dialog)
async def process_ai_dialog(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = message.text.strip()
    
    # Exit conditions
    menu_buttons = [
        "🌟 Моя натальная карта",
        "🔮 Гороскоп дня",
        "🃏 Карта Таро",
        "⭐ Pro-подписка",
        "💬 Чат с Астрологом",
    ]
    if text in menu_buttons or text.startswith("/") or text.lower() in ["выход", "/cancel", "отмена", "меню", "стоп", "назад"]:
        await state.clear()
        if text in ["выход", "/cancel", "отмена", "меню", "стоп", "назад"]:
            await message.answer("Вы вышли из режима диалога.", reply_markup=get_main_menu_keyboard())
            return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await state.clear()
        return

    sub_repo = SubscriptionRepository(session)
    is_pro = (await sub_repo.get_active_subscription(user.id)) is not None

    allowed, count, max_lim = await check_and_increment_limit(user.id, "ai", is_pro, session=session)
    if not allowed:
        await state.clear()
        await message.answer(
            "⏳ **Лимит бесплатных вопросов к ИИ-астрологу на сегодня исчерпан (1/1).**\n\n"
            "Перейдите на **Pro-подписку**, чтобы общаться с астрологом без ограничений!",
            reply_markup=get_pro_promo_keyboard(),
            parse_mode="Markdown",
        )
        return

    # Visual feedback: bot is typing
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    chart_repo = ChartRepository(session)
    chart = await chart_repo.get_by_user_id(user.id)
    chart_data = chart.chart_data if chart else None
    transits = get_current_transits(chart_data) if chart_data else None

    # Load history
    chat_repo = ChatRepository(session)
    recent_history = await chat_repo.get_recent_messages(user.id, limit=6)

    # Build prompt messages
    sys_prompt = build_system_prompt(chart_data, transits)
    messages_payload = [{"role": "system", "content": sys_prompt}]

    for msg in recent_history:
        messages_payload.append({"role": msg.role, "content": msg.content})

    messages_payload.append({"role": "user", "content": text})

    # Call AI
    ai_answer = await generate_ai_response(messages_payload)

    # Save to DB
    await chat_repo.add_message(user.id, "user", text)
    await chat_repo.add_message(user.id, "assistant", ai_answer)

    await message.answer(ai_answer, parse_mode="Markdown")
