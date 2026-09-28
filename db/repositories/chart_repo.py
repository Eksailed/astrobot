from datetime import date, time
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.natal_chart import NatalChart


class ChartRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> NatalChart | None:
        query = select(NatalChart).where(NatalChart.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save_or_update(
        self,
        user_id: int,
        birth_date: date,
        birth_time: time | None,
        birth_place: str,
        latitude: float,
        longitude: float,
        timezone_str: str,
        sun_sign: str,
        moon_sign: str,
        ascendant: str | None,
        chart_data: dict[str, Any],
    ) -> NatalChart:
        chart = await self.get_by_user_id(user_id)
        if chart is None:
            chart = NatalChart(user_id=user_id)
            self.session.add(chart)

        chart.birth_date = birth_date
        chart.birth_time = birth_time
        chart.birth_place = birth_place
        chart.latitude = latitude
        chart.longitude = longitude
        chart.timezone_str = timezone_str
        chart.sun_sign = sun_sign
        chart.moon_sign = moon_sign
        chart.ascendant = ascendant
        chart.chart_data = chart_data

        await self.session.commit()
        await self.session.refresh(chart)
        return chart
