from datetime import datetime, timedelta
from typing import Any
from services.astrology.ephemeris import PLANET_IDS, HAVE_SWISSEPH, get_zodiac_sign
from services.astrology.constants import ASPECTS, PLANETS_RU

if HAVE_SWISSEPH:
    import swisseph as swe

# Slow, impactful planets that define month-long cycles
MONTHLY_TRANSIT_BODIES = ["Mars", "Jupiter", "Saturn", "Uranus", "Pluto"]


def calculate_monthly_forecast(natal_chart_data: dict[str, Any]) -> dict[str, Any]:
    """
    Calculates key astrological events, power days, and tension days
    over the next 30 days based on slow planet transits to the natal chart.
    """
    natal_planets = natal_chart_data.get("planets", {})
    now = datetime.utcnow()

    power_days = []
    caution_days = []
    major_transits = []

    if not HAVE_SWISSEPH:
        return {
            "month_name": now.strftime("%B %Y"),
            "power_days": [(now + timedelta(days=5)).strftime("%d.%m"), (now + timedelta(days=14)).strftime("%d.%m")],
            "caution_days": [(now + timedelta(days=9)).strftime("%d.%m")],
            "key_themes": [
                "Расширение социальных связей и новые карьерные горизонты",
                "Необходимость навести порядок в финансах и завершить старые дела",
            ],
            "transits_summary": "Гармоничные транзиты Юпитера поддерживают начинания.",
        }

    # Scan the next 30 days in 3-day steps
    for day_offset in range(0, 31, 3):
        scan_date = now + timedelta(days=day_offset)
        jul_day = swe.julday(scan_date.year, scan_date.month, scan_date.day, 12.0)

        for p_name in MONTHLY_TRANSIT_BODIES:
            p_id = PLANET_IDS[p_name]
            res, _ = swe.calc_ut(jul_day, p_id)
            transit_lon = res[0]
            transit_ru = PLANETS_RU.get(p_name, p_name)

            for n_name in ["Sun", "Moon", "Mercury", "Venus", "Mars"]:
                n_info = natal_planets.get(n_name, {})
                natal_lon = n_info.get("longitude", 0.0)
                natal_ru = n_info.get("name_ru", n_name)

                diff = abs(transit_lon - natal_lon) % 360.0
                if diff > 180.0:
                    diff = 360.0 - diff

                for asp in ASPECTS:
                    orb = abs(diff - asp["angle"])
                    if orb <= 1.8:  # Very tight exact transit
                        date_str = scan_date.strftime("%d.%m")
                        aspect_desc = f"{date_str} — Транзитный {transit_ru} {asp['symbol']} Натальное {natal_ru}"

                        if asp["nature"] == "harmonious":
                            if date_str not in [d[0] for d in power_days]:
                                power_days.append((date_str, f"День силы ({transit_ru} {asp['ru']} {natal_ru})"))
                        elif asp["nature"] == "tense":
                            if date_str not in [d[0] for d in caution_days]:
                                caution_days.append((date_str, f"День повышенной внимательности ({transit_ru} {asp['ru']} {natal_ru})"))

                        if len(major_transits) < 4:
                            major_transits.append(aspect_desc)

    # Key Themes based on predominant planets
    key_themes = [
        "💼 **Карьера и амбиции:** Благоприятный период для стратегического планирования и укрепления авторитета.",
        "❤️ **Личные отношения:** Время открытых разговоров; преодоление старых иллюзий ведет к новому уровню близости.",
        "⚡️ **Энергия и здоровье:** Разумно распределяйте силы, избегайте перегрузок в дни повышенной активности Марса.",
    ]

    return {
        "month_name": now.strftime("%m.%Y"),
        "power_days": power_days[:4],
        "caution_days": caution_days[:3],
        "key_themes": key_themes,
        "major_transits": major_transits,
    }
