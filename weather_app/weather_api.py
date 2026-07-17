from typing import Any

import httpx

from weather_app.config import (
    GEOCODING_API_URL,
    REVERSE_GEOCODING_API_URL,
    REVERSE_GEOCODING_USER_AGENT,
    WEATHER_API_URL,
)
from weather_app.data.translations import TRANSLATIONS


def get_coordinates(city: str, country: str | None = None, lang: str = "en") -> dict[str, Any] | None:
    query = city.strip()
    if not query: return None
    if country and country.strip(): query += f", {country.strip()}"

    # The geocoding API's "language" param doesn't just pick the display language of
    # results, it also restricts which name variants get matched at all (e.g. a
    # Cyrillic query only matches under language=bg, never under language=en). Try
    # the current UI language first, then fall back to the other supported language,
    # so a city can be found no matter which script/language it was typed in.
    for search_lang in dict.fromkeys([lang, "bg", "en"]):
        params: dict[str, Any] = {"name": query, "count": 1, "language": search_lang, "format": "json"}
        try:
            response = httpx.get(GEOCODING_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "results" in data and data["results"]:
                return data["results"][0]
        except Exception:
            continue
    return None

def reverse_geocode(lat: float, lon: float, lang: str = "en") -> dict[str, str] | None:
    """Resolve a display name and country for coordinates via OpenStreetMap Nominatim."""
    params: dict[str, Any] = {"lat": lat, "lon": lon, "format": "jsonv2", "accept-language": lang}
    headers = {"User-Agent": REVERSE_GEOCODING_USER_AGENT}
    try:
        response = httpx.get(REVERSE_GEOCODING_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        address = data.get("address", {})
        name = address.get("city") or address.get("town") or address.get("village") or address.get("county")
        country = address.get("country")
        if not country:
            return None
        # Rural coordinates can resolve to a country with no city/town/village/county;
        # still surface the known country rather than discarding it entirely.
        return {"name": name or "", "country": country}
    except Exception:
        return None

def build_location_from_coordinates(lat: float, lon: float, lang: str = "en") -> dict[str, Any]:
    """Build a location dict (matching get_coordinates' shape) directly from browser-provided coordinates."""
    resolved = reverse_geocode(lat, lon, lang)
    if resolved:
        display_name = resolved["name"] or TRANSLATIONS[lang]["geo_header_generic"]
        return {"name": display_name, "country": resolved["country"], "latitude": lat, "longitude": lon}
    return {"name": TRANSLATIONS[lang]["geo_header_generic"], "country": "", "latitude": lat, "longitude": lon}

def get_weather_data(lat: float, lon: float) -> dict[str, Any] | None:
    f_params: dict[str, Any] = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
        "hourly": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,precipitation_probability,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,weather_code,precipitation_probability_max,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": 16
    }

    try:
        f_resp = httpx.get(WEATHER_API_URL, params=f_params, timeout=10)
        f_resp.raise_for_status()
        return f_resp.json()
    except Exception:
        return None
