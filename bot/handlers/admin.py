import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.models.user import User
from db.models.natal_chart import NatalChart
from db.models.subscription import Subscription
from db.repositories.subscription_repo import SubscriptionRepository
from bot.states.admin import AdminState

logger = logging.getLogger("astro_bot.admin")
router = Router(name="admin_handlers")


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Рассылка всем", callback_data="admin_broadcast"),
                InlineKeyboardButton(text="⭐️ Выдать Pro", callback_data="admin_grant_pro"),
            ],
            [
                InlineKeyboardButton(text="📋 Последние юзеры", callback_data="admin_recent_users"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_refresh"),
            ],
            [
                InlineKeyboardButton(text="❌ Закрыть панель", callback_data="admin_close"),
            ],
        ]
    )


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Подтвердить и отправить", callback_data="admin_confirm_send"),
            ],
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="admin_cancel_broadcast"),
            ],
        ]
    )


async def build_stats_text(session: AsyncSession) -> str:
    # 1. Total users
    total_users = await session.scalar(select(func.count(User.id))) or 0

    # 2. Users with completed chart
    total_charts = await session.scalar(select(func.count(NatalChart.id))) or 0

    # 3. Active Pro users
    now = datetime.utcnow()
    active_pros = await session.scalar(
        select(func.count(Subscription.id)).where(
            Subscription.is_active == True,
            Subscription.expires_at > now,
        )
    ) or 0

    # 4. Today's new registrations
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_users = await session.scalar(
        select(func.count(User.id)).where(User.created_at >= today_start)
    ) or 0

    # 5. Conversion rate
    conv_chart = (total_charts / total_users * 100) if total_users > 0 else 0.0
    conv_pro = (active_pros / total_users * 100) if total_users > 0 else 0.0

    return (
        "👑 <b>Панель управления AstroBot</b>\n\n"
        "📊 <b>Ключевые бизнес-метрики:</b>\n"
        f"• Всего пользователей: <b>{total_users:,}</b>\n"
        f"• Новых за сегодня: <b>+{today_users}</b>\n"
        f"• Заполнили профиль (карта): <b>{total_charts:,}</b> (конверсия {conv_chart:.1f}%)\n"
        f"• Активных PRO-подписчиков: <b>{active_pros}</b> (конверсия {conv_pro:.1f}%)\n\n"
        f"💰 Оценочный MRR (Stars): <b>{active_pros * settings.PRO_PRICE_STARS:,} ⭐️</b> (~{active_pros * 299:,} ₽)\n"
        f"🕒 Серверное время: <code>{now.strftime('%d.%m.%Y %H:%M:%S UTC')}</code>"
    )


@router.message(Command("admin"), StateFilter("*"))
async def cmd_admin(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    if not settings.is_admin(user_id):
        await message.answer("⛔️ У вас нет прав доступа к панели администратора.")
        return

    text = await build_stats_text(session)
    await message.answer(text, reply_markup=get_admin_keyboard())


@router.callback_query(F.data == "admin_refresh")
async def cb_admin_refresh(callback: CallbackQuery, session: AsyncSession) -> None:
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    text = await build_stats_text(session)
    try:
        await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
    except Exception:
        pass
    await callback.answer("Данные обновлены ✓")


@router.callback_query(F.data == "admin_close")
async def cb_admin_close(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "admin_recent_users")
async def cb_admin_recent_users(callback: CallbackQuery, session: AsyncSession) -> None:
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    stmt = select(User).order_by(desc(User.created_at)).limit(10)
    result = await session.execute(stmt)
    users = result.scalars().all()

    if not users:
        await callback.answer("Пока нет зарегистрированных пользователей.", show_alert=True)
        return

    lines = ["📋 <b>Последние 10 пользователей:</b>\n"]
    for u in users:
        uname = f"@{u.username}" if u.username else f"ID {u.telegram_id}"
        reg_time = u.created_at.strftime("%d.%m %H:%M")
        chart_icon = "🪐" if u.natal_chart else "▫️"
        lines.append(f"• {uname} ({u.first_name or '—'}) | {chart_icon} | {reg_time}")

    lines.append("\n<i>Легенда: 🪐 — рассчитал карту, ▫️ — только запустил</i>")
    await callback.message.answer("\n".join(lines))
    await callback.answer()


# ==========================================
# Broadcast (Рассылка)
# ==========================================

@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_broadcast_text)
    await callback.message.answer(
        "📢 <b>Режим рассылки сообщений</b>\n\n"
        "Отправьте текст сообщения для рассылки всем пользователям бота.\n"
        "Поддерживается HTML-разметка.\n\n"
        "<i>Для отмены отправьте /cancel или Назад.</i>"
    )
    await callback.answer()


@router.message(AdminState.waiting_for_broadcast_text)
async def process_broadcast_text(message: Message, state: FSMContext) -> None:
    if message.text in ["/cancel", "Назад", "Отмена", "/admin"]:
        await state.clear()
        await message.answer("Рассылка отменена.")
        return

    broadcast_text = message.html_text if message.html_text else message.text
    await state.update_data(broadcast_text=broadcast_text)
    await state.set_state(AdminState.confirm_broadcast)

    preview_header = "🔎 <b>Предпросмотр сообщения для рассылки:</b>\n" + "—" * 25 + "\n\n"
    preview_footer = "\n\n" + "—" * 25 + "\nПодтвердите отправку всем пользователям базы:"

    await message.answer(
        preview_header + broadcast_text + preview_footer,
        reply_markup=get_broadcast_confirm_keyboard(),
    )


@router.callback_query(F.data == "admin_cancel_broadcast")
async def cb_cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена администратором.")
    await callback.answer()


@router.callback_query(F.data == "admin_confirm_send")
async def cb_confirm_send_broadcast(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    data = await state.get_data()
    broadcast_text = data.get("broadcast_text")
    if not broadcast_text:
        await callback.answer("Текст рассылки утерян. Попробуйте снова.", show_alert=True)
        await state.clear()
        return

    await state.clear()
    await callback.message.edit_text("⏳ <b>Рассылка запущена... Пожалуйста, подождите.</b>")

    # Fetch all user telegram IDs
    stmt = select(User.telegram_id)
    result = await session.execute(stmt)
    user_ids = result.scalars().all()

    total = len(user_ids)
    success = 0
    blocked = 0
    errors = 0

    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=broadcast_text)
            success += 1
            await asyncio.sleep(0.04)  # ~25 messages/sec safe rate
        except TelegramForbiddenError:
            blocked += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_message(chat_id=uid, text=broadcast_text)
                success += 1
            except Exception:
                errors += 1
        except TelegramAPIError as e:
            logger.warning(f"Failed to send broadcast to {uid}: {e}")
            errors += 1
        except Exception as e:
            logger.error(f"Unexpected error broadcasting to {uid}: {e}")
            errors += 1

    report = (
        "📢 <b>Отчет о завершении рассылки:</b>\n\n"
        f"• Всего получателей: <b>{total}</b>\n"
        f"• ✅ Успешно доставлено: <b>{success}</b>\n"
        f"• 🚫 Заблокировали бота: <b>{blocked}</b>\n"
        f"• ⚠️ Ошибок отправки: <b>{errors}</b>"
    )
    await callback.message.answer(report, reply_markup=get_admin_keyboard())
    await callback.answer()


# ==========================================
# Grant PRO manually
# ==========================================

@router.callback_query(F.data == "admin_grant_pro")
async def cb_admin_grant_pro(callback: CallbackQuery, state: FSMContext) -> None:
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_grant_pro)
    await callback.message.answer(
        "⭐️ <b>Выдача PRO-подписки</b>\n\n"
        "Отправьте данные в формате:\n"
        "<code>TELEGRAM_ID ДНИ</code>\n\n"
        "<i>Пример: <code>123456789 30</code> (выдать на 30 дней)</i>\n"
        "Для отмены отправьте /cancel"
    )
    await callback.answer()


@router.message(AdminState.waiting_for_grant_pro)
async def process_grant_pro(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if message.text in ["/cancel", "Назад", "Отмена"]:
        await state.clear()
        await message.answer("Действие отменено.")
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await message.answer(
            "⚠️ Неверный формат! Введите: <code>TELEGRAM_ID ДНИ</code> (например: <code>123456789 30</code>):"
        )
        return

    target_tg_id = int(parts[0])
    days = int(parts[1])

    # Find user
    stmt = select(User).where(User.telegram_id == target_tg_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await message.answer(f"Пользователь с Telegram ID <code>{target_tg_id}</code> не найден в базе данных.")
        return

    sub_repo = SubscriptionRepository(session)
    await sub_repo.create_subscription(
        user_id=user.id,
        plan="pro_admin",
        days=days,
        telegram_charge_id=f"admin_{message.from_user.id}_{int(datetime.utcnow().timestamp())}",
    )
    await session.commit()
    await state.clear()

    # Notify target user
    try:
        await bot.send_message(
            chat_id=target_tg_id,
            text=(
                f"🎉 <b>Вам активирован PRO-доступ на {days} дней!</b>\n\n"
                "⭐️ Вам открыты все безлимитные функции: Таро, совместимость, прогноз на месяц и чат с ИИ-астрологом!"
            ),
        )
    except Exception as e:
        logger.warning(f"Could not notify user {target_tg_id} about granted Pro: {e}")

    await message.answer(
        f"✅ <b>PRO-доступ успешно выдан!</b>\n\n"
        f"• Пользователь: <code>{target_tg_id}</code>\n"
        f"• Дней: <b>{days}</b>\n"
        f"• Статус: Активен",
        reply_markup=get_admin_keyboard(),
    )


@router.message(Command("grant_pro"), StateFilter("*"))
async def cmd_quick_grant_pro(
    message: Message,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Quick command: /grant_pro <telegram_id> <days>"""
    if not settings.is_admin(message.from_user.id):
        return

    parts = message.text.strip().split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await message.answer("Формат: <code>/grant_pro TELEGRAM_ID ДНИ</code>")
        return

    target_tg_id = int(parts[1])
    days = int(parts[2])

    stmt = select(User).where(User.telegram_id == target_tg_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await message.answer(f"Юзер <code>{target_tg_id}</code> не найден в БД.")
        return

    sub_repo = SubscriptionRepository(session)
    await sub_repo.create_subscription(
        user_id=user.id,
        plan="pro_admin",
        days=days,
        telegram_charge_id=f"admin_{message.from_user.id}",
    )
    await session.commit()

    try:
        await bot.send_message(
            chat_id=target_tg_id,
            text=f"🎉 <b>Вам активирован PRO-доступ на {days} дней!</b>",
        )
    except Exception:
        pass

    await message.answer(f"✅ PRO активирован для <code>{target_tg_id}</code> на {days} дн.")
