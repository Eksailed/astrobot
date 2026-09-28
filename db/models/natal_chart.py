from datetime import date, time, datetime
from typing import Any
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class NatalChart(Base):
    __tablename__ = "natal_charts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    # Birth Data
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    birth_place: Mapped[str] = mapped_column(String(256), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    timezone_str: Mapped[str] = mapped_column(String(64), nullable=False)

    # Calculated core signs
    sun_sign: Mapped[str] = mapped_column(String(32), nullable=False)
    moon_sign: Mapped[str] = mapped_column(String(32), nullable=False)
    ascendant: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Full details: planets degrees, houses, aspects
    chart_data: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="natal_chart")
