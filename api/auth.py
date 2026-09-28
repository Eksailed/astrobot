import hmac
import hashlib
import json
import logging
from urllib.parse import parse_qsl
from fastapi import Header
from core.config import settings

logger = logging.getLogger("astro_app.auth")


def validate_telegram_data(init_data: str) -> dict | None:
    """
    Validates Telegram WebApp initData string using HMAC-SHA256.
    """
    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
        if "hash" not in parsed_data:
            return None

        received_hash = parsed_data.pop("hash")
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if calculated_hash == received_hash:
            user_json = parsed_data.get("user")
            if user_json:
                parsed_data["user"] = json.loads(user_json)
            return parsed_data
    except Exception as e:
        logger.debug(f"validate_telegram_data exception: {e}")
    return None


async def get_current_telegram_user(
    x_telegram_init_data: str | None = Header(None, alias="X-Telegram-Init-Data"),
    authorization: str | None = Header(None, alias="Authorization"),
    x_telegram_user_id: str | None = Header(None, alias="X-Telegram-User-Id"),
) -> dict:
    raw_data = x_telegram_init_data
    if not raw_data and authorization:
        if authorization.startswith("tma "):
            raw_data = authorization[4:].strip()
        elif authorization.startswith("Bearer "):
            raw_data = authorization[7:].strip()
        else:
            raw_data = authorization.strip()

    # 1. Try official HMAC validation
    if raw_data:
        validated = validate_telegram_data(raw_data)
        if validated and validated.get("user"):
            return validated["user"]

        # 2. Extract user JSON from initData query params
        try:
            parsed_data = dict(parse_qsl(raw_data, keep_blank_values=True))
            if "user" in parsed_data:
                user_dict = json.loads(parsed_data["user"])
                if "id" in user_dict:
                    return user_dict
        except Exception:
            pass

    # 3. Use client-provided header from initDataUnsafe
    if x_telegram_user_id and x_telegram_user_id.isdigit():
        return {"id": int(x_telegram_user_id), "first_name": "User", "username": None}

    # 4. Fallback for testing in direct browser outside Telegram
    return {"id": 123456789, "first_name": "TestUser", "username": "test_astrologer"}
