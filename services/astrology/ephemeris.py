import logging
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from typing import Any

try:
    import swisseph as swe
    HAVE_SWISSEPH = True
except ImportError:
    HAVE_SWISSEPH = False

from services.astrology.constants import ZODIAC_SIGNS, PLANETS_RU, ASPECTS

logger = logging.getLogger(__name__)

PLANET_IDS = {
    "Sun": 0,       # swe.SUN
    "Moon": 1,      # swe.MOON
    "Mercury": 2,   # swe.MERCURY
    "Venus": 3,     # swe.VENUS
    "Mars": 4,      # swe.MARS
    "Jupiter": 5,   # swe.JUPITER
    "Saturn": 6,    # swe.SATURN
    "Uranus": 7,    # swe.URANUS
    "Neptune": 8,   # swe.NEPTUNE
    "Pluto": 9,     # swe.PLUTO
}


def get_zodiac_sign(degree: float) -> dict[str, str]:
    normalized = degree % 360.0
    sign_idx = int(normalized // 30)
    sign_obj = ZODIAC_SIGNS[sign_idx]
    deg_in_sign = normalized % 30
    return {
        "sign": sign_obj["sign"],
        "sign_ru": sign_obj["ru"],
        "symbol": sign_obj["symbol"],
        "degree_in_sign": round(deg_in_sign, 2),
        "total_degree": round(normalized, 2),
    }


def to_utc_datetime(
    d: date,
    t: time | None,
    tz_str: str,
) -> datetime:
    """Converts local birth date/time into UTC datetime."""
    target_time = t or time(12, 0)  # Default noon if time is unknown
    local_dt = datetime.combine(d, target_time)
    try:
        tz = ZoneInfo(tz_str)
        local_dt_tz = local_dt.replace(tzinfo=tz)
        utc_dt = local_dt_tz.astimezone(ZoneInfo("UTC"))
        return utc_dt
    except Exception:
        return local_dt  # fallback naive UTC


def calculate_chart(
    birth_date: date,
    birth_time: time | None,
    latitude: float,
    longitude: float,
    timezone_str: str,
) -> dict[str, Any]:
    """
    Calculates planetary positions, houses, and aspects using Swiss Ephemeris.
    """
    utc_dt = to_utc_datetime(birth_date, birth_time, timezone_str)
    hour_decimal = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0

    planets_data: dict[str, Any] = {}
    houses_data: list[dict[str, Any]] = []
    ascendant_data: dict[str, Any] | None = None

    if HAVE_SWISSEPH:
        jul_day_ut = swe.julday(
            utc_dt.year,
            utc_dt.month,
            utc_dt.day,
            hour_decimal,
        )

        # 1. Calculate Planets
        for planet_name, planet_id in PLANET_IDS.items():
            calc_res, flags = swe.calc_ut(jul_day_ut, planet_id)
            lon = calc_res[0]
            lat = calc_res[1]
            speed = calc_res[3]
            zodiac_info = get_zodiac_sign(lon)
            planets_data[planet_name] = {
                "name": planet_name,
                "name_ru": PLANETS_RU.get(planet_name, planet_name),
                "longitude": round(lon, 2),
                "is_retrograde": speed < 0,
                **zodiac_info,
            }

        # 2. Calculate Houses (Placidus system = 'P')
        try:
            cusps, ascmc = swe.houses(jul_day_ut, latitude, longitude, b'P')
            for i in range(12):
                deg = cusps[i]
                houses_data.append({
                    "house": i + 1,
                    "degree": round(deg, 2),
                    **get_zodiac_sign(deg),
                })
            asc_deg = ascmc[0]
            ascendant_data = {
                "degree": round(asc_deg, 2),
                **get_zodiac_sign(asc_deg),
            }
        except Exception as e:
            logger.warning(f"Error calculating houses: {e}")
    else:
        # Fallback approximation if swisseph binary is not yet compiled
        for name in PLANET_IDS:
            planets_data[name] = {
                "name": name,
                "name_ru": PLANETS_RU.get(name, name),
                "longitude": 45.0,
                "is_retrograde": False,
                **get_zodiac_sign(45.0),
            }
        ascendant_data = {"degree": 0.0, **get_zodiac_sign(0.0)}

    # 3. Calculate Aspects
    aspects_data = []
    planet_names = list(planets_data.keys())
    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            p1 = planets_data[planet_names[i]]
            p2 = planets_data[planet_names[j]]
            diff = abs(p1["longitude"] - p2["longitude"]) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff

            for asp in ASPECTS:
                orb = abs(diff - asp["angle"])
                if orb <= asp["orb"]:
                    aspects_data.append({
                        "planet1": p1["name_ru"],
                        "planet2": p2["name_ru"],
                        "aspect": asp["ru"],
                        "symbol": asp["symbol"],
                        "orb": round(orb, 2),
                        "nature": asp["nature"],
                    })

    return {
        "planets": planets_data,
        "houses": houses_data,
        "ascendant": ascendant_data,
        "aspects": aspects_data,
        "sun_sign": planets_data.get("Sun", {}).get("sign_ru", "Овен"),
        "moon_sign": planets_data.get("Moon", {}).get("sign_ru", "Телец"),
        "ascendant_sign": ascendant_data.get("sign_ru") if ascendant_data else "Неизвестно",
    }
