from datetime import datetime, date, time
from typing import Any
from services.astrology.ephemeris import calculate_chart, PLANET_IDS, get_zodiac_sign, HAVE_SWISSEPH
from services.astrology.constants import ASPECTS, PLANETS_RU

if HAVE_SWISSEPH:
    import swisseph as swe


def get_current_transits(natal_chart_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Calculates current planetary positions and compares them with natal planets.
    """
    now = datetime.utcnow()
    hour_decimal = now.hour + now.minute / 60.0 + now.second / 3600.0

    transit_aspects = []
    natal_planets = natal_chart_data.get("planets", {})

    if not HAVE_SWISSEPH:
        return [
            {
                "transit_planet": "Луна",
                "natal_planet": "Солнце",
                "aspect": "Трин",
                "symbol": "△",
                "orb": 1.2,
                "nature": "harmonious",
            }
        ]

    jul_day_ut = swe.julday(now.year, now.month, now.day, hour_decimal)

    for p_name, p_id in PLANET_IDS.items():
        res, _ = swe.calc_ut(jul_day_ut, p_id)
        transit_lon = res[0]
        transit_ru = PLANETS_RU.get(p_name, p_name)

        # Check aspect with each natal planet
        for n_name, n_info in natal_planets.items():
            natal_lon = n_info.get("longitude", 0.0)
            natal_ru = n_info.get("name_ru", n_name)

            diff = abs(transit_lon - natal_lon) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff

            for asp in ASPECTS:
                # Transits usually have tighter orbs (within 2-3 degrees)
                transit_orb = min(asp["orb"], 3.0)
                orb = abs(diff - asp["angle"])
                if orb <= transit_orb:
                    transit_aspects.append({
                        "transit_planet": transit_ru,
                        "natal_planet": natal_ru,
                        "aspect": asp["ru"],
                        "symbol": asp["symbol"],
                        "orb": round(orb, 2),
                        "nature": asp["nature"],
                    })

    return transit_aspects


def format_chart_summary(chart_data: dict[str, Any]) -> str:
    """
    Prepares a compact text summary of the natal chart for the AI prompt.
    """
    planets = chart_data.get("planets", {})
    sun = planets.get("Sun", {})
    moon = planets.get("Moon", {})
    asc = chart_data.get("ascendant", {})

    sun_str = f"Солнце в {sun.get('sign_ru', 'знаке')} ({sun.get('degree_in_sign', 0)}°)"
    moon_str = f"Луна в {moon.get('sign_ru', 'знаке')} ({moon.get('degree_in_sign', 0)}°)"
    asc_str = f"Асцендент в {asc.get('sign_ru', 'знаке')}" if asc else ""

    key_planets = []
    for p_name in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
        p = planets.get(p_name)
        if p:
            retro = " (R)" if p.get("is_retrograde") else ""
            key_planets.append(f"{p.get('name_ru')}: {p.get('sign_ru')}{retro}")

    aspects = chart_data.get("aspects", [])[:5]  # Top 5 tightest aspects
    aspect_strs = [
        f"{a['planet1']} {a['aspect']} {a['planet2']} (орб {a['orb']}°)"
        for a in aspects
    ]

    summary = (
        f"- Ядро личности: {sun_str}, {moon_str}, {asc_str}\n"
        f"- Личные планеты: {', '.join(key_planets)}\n"
        f"- Ключевые натальные аспекты: {'; '.join(aspect_strs) if aspect_strs else 'спокойные'}"
    )
    return summary
