from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from core.config import settings


def get_consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Мне есть 18 лет и я согласен(сна)",
                    callback_data="consent_accept",
                )
            ]
        ]
    )


def get_main_menu_keyboard(webapp_url: str = settings.WEBAPP_URL) -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="🌟 Моя натальная карта"),
            KeyboardButton(text="🔮 Гороскоп дня"),
        ],
        [
            KeyboardButton(text="🃏 Карта Таро"),
            KeyboardButton(text="💬 Чат с Астрологом"),
        ],
        [
            KeyboardButton(text="💞 Совместимость"),
            KeyboardButton(text="⭐ Pro-подписка"),
        ],
        [
            KeyboardButton(text="📱 Открыть Mini App", web_app=WebAppInfo(url=webapp_url)),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_skip_time_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏳ Не знаю точное время (расчет на 12:00)")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_pro_invoice_keyboard(price_stars: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⭐️ Оформить Pro за {price_stars} Stars",
                    pay=True,
                )
            ]
        ]
    )


def get_pro_promo_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐️ Получить Pro (без лимитов)",
                    callback_data="buy_pro",
                )
            ]
        ]
    )


def get_tarot_menu_keyboard(is_pro: bool) -> InlineKeyboardMarkup:
    pro_badge = "" if is_pro else " ⭐️"
    kb = [
        [
            InlineKeyboardButton(text="🃏 Карта Дня", callback_data="tarot_day"),
        ],
        [
            InlineKeyboardButton(text="🔮 Прошлое / Настоящее / Будущее", callback_data="tarot_three"),
        ],
        [
            InlineKeyboardButton(text=f"❤️ Любовь и Отношения{pro_badge}", callback_data="tarot_love"),
        ],
        [
            InlineKeyboardButton(text=f"💼 Карьера и Финансы{pro_badge}", callback_data="tarot_career"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_synastry_choice_keyboard(bot_username: str, user_id: int) -> InlineKeyboardMarkup:
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}?start=syn_{user_id}&text=Давай проверим нашу астрологическую совместимость! ✨"
    kb = [
        [
            InlineKeyboardButton(text="✍️ Ввести данные партнера вручную", callback_data="synastry_manual"),
        ],
        [
            InlineKeyboardButton(text="📲 Отправить ссылку партнеру", url=share_url),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
