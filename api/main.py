from datetime import datetime, date, time
from typing import Any
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db_session
from db.repositories.user_repo import UserRepository
from db.repositories.chart_repo import ChartRepository
from db.repositories.subscription_repo import SubscriptionRepository
from services.astrology.geocoding import resolve_location
from services.astrology.ephemeris import calculate_chart
from services.astrology.chart_calculator import get_current_transits
from services.tarot.spreads import draw_card_of_the_day, draw_three_cards_spread
from services.limits import check_and_increment_limit
from api.auth import get_current_telegram_user

app = FastAPI(title="AstroBot Mini App API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BirthDataRequest(BaseModel):
    birth_date: date
    birth_time: str | None = Field(default=None, description="HH:MM or None")
    city: str


@app.get("/api/me")
async def get_me(
    current_user: dict = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(
        telegram_id=current_user["id"],
        username=current_user.get("username"),
        first_name=current_user.get("first_name"),
    )

    chart_repo = ChartRepository(session)
    chart = await chart_repo.get_by_user_id(user.id)

    sub_repo = SubscriptionRepository(session)
    sub = await sub_repo.get_active_subscription(user.id)

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "is_pro": sub is not None,
        "pro_expires_at": sub.expires_at if sub else None,
        "has_chart": chart is not None,
        "chart": {
            "sun_sign": chart.sun_sign,
            "moon_sign": chart.moon_sign,
            "ascendant": chart.ascendant,
            "birth_place": chart.birth_place,
            "chart_data": chart.chart_data,
        } if chart else None,
    }


@app.post("/api/chart/calculate")
async def calculate_and_save_chart(
    data: BirthDataRequest,
    current_user: dict = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(
        telegram_id=current_user["id"],
        username=current_user.get("username"),
        first_name=current_user.get("first_name"),
    )

    loc = await resolve_location(data.city)

    parsed_time = None
    if data.birth_time:
        try:
            parsed_time = datetime.strptime(data.birth_time, "%H:%M").time()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

    chart_data = calculate_chart(
        birth_date=data.birth_date,
        birth_time=parsed_time,
        latitude=loc.latitude,
        longitude=loc.longitude,
        timezone_str=loc.timezone_str,
    )

    chart_repo = ChartRepository(session)
    saved = await chart_repo.save_or_update(
        user_id=user.id,
        birth_date=data.birth_date,
        birth_time=parsed_time,
        birth_place=loc.place_name,
        latitude=loc.latitude,
        longitude=loc.longitude,
        timezone_str=loc.timezone_str,
        sun_sign=chart_data["sun_sign"],
        moon_sign=chart_data["moon_sign"],
        ascendant=chart_data["ascendant_sign"],
        chart_data=chart_data,
    )

    return {
        "status": "success",
        "sun_sign": saved.sun_sign,
        "moon_sign": saved.moon_sign,
        "ascendant": saved.ascendant,
        "chart_data": chart_data,
    }


@app.get("/api/tarot/card-of-day")
async def get_tarot_card_of_day(
    current_user: dict = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(current_user["id"])

    sub_repo = SubscriptionRepository(session)
    is_pro = (await sub_repo.get_active_subscription(user.id)) is not None

    allowed, count, max_lim = await check_and_increment_limit(user.id, "tarot", is_pro)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Бесплатный суточный лимит исчерпан. Оформите PRO для снятия ограничений."
        )

    drawn = draw_card_of_the_day()
    return {
        "card_id": drawn.card.id,
        "name_ru": drawn.card.name_ru,
        "name_en": drawn.card.name_en,
        "is_reversed": drawn.is_reversed,
        "position": drawn.position_str,
        "meaning": drawn.meaning,
        "keywords": drawn.card.keywords,
    }
