import logging
from dataclasses import dataclass
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

logger = logging.getLogger(__name__)

tf = TimezoneFinder()
geolocator = Nominatim(user_agent="astro_bot_geocoder")

# Default fallback coordinates (Moscow)
DEFAULT_LAT = 55.7558
DEFAULT_LON = 37.6173
DEFAULT_TZ = "Europe/Moscow"


@dataclass
class LocationInfo:
    place_name: str
    latitude: float
    longitude: float
    timezone_str: str


async def resolve_location(city_name: str) -> LocationInfo:
    """
    Geocodes city name into coordinates and discovers its IANA timezone.
    """
    clean_city = city_name.strip()
    try:
        # Nominatim lookup
        location = geolocator.geocode(clean_city, language="ru")
        if location:
            lat = location.latitude
            lon = location.longitude
            tz_str = tf.timezone_at(lng=lon, lat=lat) or DEFAULT_TZ
            return LocationInfo(
                place_name=location.address.split(",")[0],
                latitude=lat,
                longitude=lon,
                timezone_str=tz_str,
            )
    except Exception as e:
        logger.warning(f"Geocoding error for '{city_name}': {e}. Using fallback.")

    return LocationInfo(
        place_name=clean_city or "Москва",
        latitude=DEFAULT_LAT,
        longitude=DEFAULT_LON,
        timezone_str=DEFAULT_TZ,
    )
