import hmac
import hashlib
import json
from urllib.parse import parse_qsl, unquote
from fastapi import HTTPException, Header, Depends
from core.config import settings


def validate_telegram_data(init_data: str) -> dict:
    """
    Validates Telegram WebApp initData string using HMAC-SHA256.
    """
    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid initData format")

    if "hash" not in parsed_data:
        raise HTTPException(status_code=401, detail="Hash missing from initData")

    received_hash = parsed_data.pop("hash")

    # Sort key-value pairs alphabetically and format as 'key=value\n'
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))

    # Secret key is HMAC-SHA256 of bot token with key "WebAppData"
    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()

    # Calculate HMAC
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if calculated_hash != received_hash:
        raise HTTPException(status_code=403, detail="Invalid initData signature")

    user_json = parsed_data.get("user")
    if user_json:
        parsed_data["user"] = json.loads(user_json)

    return parsed_data


async def get_current_telegram_user(
    x_telegram_init_data: str | None = Header(None, alias="X-Telegram-Init-Data")
) -> dict:
    if not x_telegram_init_data:
        # Development fallback mode
        return {"id": 123456789, "first_name": "TestUser", "username": "test_astrologer"}

    data = validate_telegram_data(x_telegram_init_data)
    user_info = data.get("user")
    if not user_info:
        raise HTTPException(status_code=400, detail="User not found in initData")
    return user_info
