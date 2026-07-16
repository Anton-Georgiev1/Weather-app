import html
from datetime import datetime
from typing import Any, Literal

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
import httpx
import pandas as pd
from streamlit_geolocation import streamlit_geolocation  # pyright: ignore[reportMissingTypeStubs]
from streamlit_local_storage import LocalStorage  # pyright: ignore[reportMissingTypeStubs]

AlertSeverity = Literal["warning", "error"]

# --- Configuration ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
REVERSE_GEOCODING_API_URL = "https://nominatim.openstreetmap.org/reverse"
REVERSE_GEOCODING_USER_AGENT = "WeatherAppStreamlit/1.0 (+https://github.com/Anton-Georgiev1/Weather-app)"
SKYWATCH_URL = "https://skywatchbg.vercel.app/"
LAST_CITY_STORAGE_KEY = "last_city"
LAST_COUNTRY_STORAGE_KEY = "last_country"
LAST_LANG_STORAGE_KEY = "last_lang"

# Seasonal color palettes, ported from seasonal-themes.html. Each value is injected
# as a CSS custom property so the same stylesheet can re-skin the whole app per season.
SEASON_THEMES: dict[str, dict[str, str]] = {
    "spring": {
        "emoji": "🌸",
        "label_en": "Spring",
        "label_bg": "Пролет",
        "page_bg": "linear-gradient(160deg, #f2f7f0, #f7eef3)",
        "surface": "#fcfdfb",
        "border": "#d7ddd4",
        "text": "#2b332c",
        "accent": "#4d9e5f",
        "accent_deep": "#35804a",
        "accent_soft": "#e2f0e2",
        "accent_grad": "linear-gradient(135deg, #4d9e5f, #c47a9a)",
        "hero_grad": "linear-gradient(135deg, #e7f2e5, #f4ecf1)",
        "accent_shadow": "rgba(77,158,95,.30)",
        "card_shadow": "rgba(40,50,42,.08)",
    },
    "summer": {
        "emoji": "☀️",
        "label_en": "Summer",
        "label_bg": "Лято",
        "page_bg": "linear-gradient(160deg, #f7f3e6, #e9f0f7)",
        "surface": "#fdfcf6",
        "border": "#ddd6c2",
        "text": "#29303b",
        "accent": "#e0a83b",
        "accent_deep": "#b06c22",
        "accent_soft": "#f5ecd2",
        "accent_grad": "linear-gradient(135deg, #e0a83b, #4c8fc9)",
        "hero_grad": "linear-gradient(135deg, #f5eccd, #e6eef6)",
        "accent_shadow": "rgba(210,140,50,.32)",
        "card_shadow": "rgba(40,48,60,.08)",
    },
    "autumn": {
        "emoji": "🍂",
        "label_en": "Autumn",
        "label_bg": "Есен",
        "page_bg": "linear-gradient(160deg, #f5efe4, #f0e4dd)",
        "surface": "#fbf7ef",
        "border": "#d9cbb8",
        "text": "#342c25",
        "accent": "#c26a2e",
        "accent_deep": "#9c5324",
        "accent_soft": "#f0e0cd",
        "accent_grad": "linear-gradient(135deg, #c26a2e, #8a5a44)",
        "hero_grad": "linear-gradient(135deg, #f1e4cf, #ecdfd4)",
        "accent_shadow": "rgba(190,105,45,.32)",
        "card_shadow": "rgba(50,40,32,.09)",
    },
    "winter": {
        "emoji": "❄️",
        "label_en": "Winter",
        "label_bg": "Зима",
        "page_bg": "linear-gradient(160deg, #f2f4f7, #eef0f5)",
        "surface": "#fbfcfd",
        "border": "#d5dae2",
        "text": "#2b323d",
        "accent": "#5d94bd",
        "accent_deep": "#3b6d94",
        "accent_soft": "#e5ecf1",
        "accent_grad": "linear-gradient(135deg, #5d94bd, #b9c2cd)",
        "hero_grad": "linear-gradient(135deg, #e8eef3, #ebeef3)",
        "accent_shadow": "rgba(93,148,189,.30)",
        "card_shadow": "rgba(43,50,61,.08)",
    },
}

WMO_CODES = {
    0: {
        "en": ("Clear sky", "☀️"),
        "bg": ("Ясно небе", "☀️")
    },
    1: {
        "en": ("Mainly clear", "🌤️"),
        "bg": ("Предимно ясно", "🌤️")
    },
    2: {
        "en": ("Partly cloudy", "⛅"),
        "bg": ("Частична облачност", "⛅")
    },
    3: {
        "en": ("Overcast", "☁️"),
        "bg": ("Значителна облачност", "☁️")
    },
    45: {
        "en": ("Fog", "🌫️"),
        "bg": ("Мъгла", "🌫️")
    },
    48: {
        "en": ("Depositing rime fog", "🌫️"),
        "bg": ("Скрежна мъгла", "🌫️")
    },
    51: {
        "en": ("Drizzle: Light", "🌦️"),
        "bg": ("Ръмеж: Слаб", "🌦️")
    },
    53: {
        "en": ("Drizzle: Moderate", "🌦️"),
        "bg": ("Ръмеж: Умерен", "🌦️")
    },
    55: {
        "en": ("Drizzle: Dense", "🌦️"),
        "bg": ("Ръмеж: Плътен", "🌦️")
    },
    56: {
        "en": ("Freezing Drizzle: Light", "🌨️"),
        "bg": ("Леден ръмеж: Слаб", "🌨️")
    },
    57: {
        "en": ("Freezing Drizzle: Dense", "🌨️"),
        "bg": ("Леден ръмеж: Плътен", "🌨️")
    },
    61: {
        "en": ("Rain: Slight", "🌧️"),
        "bg": ("Дъжд: Слаб", "🌧️")
    },
    63: {
        "en": ("Rain: Moderate", "🌧️"),
        "bg": ("Дъжд: Умерен", "🌧️")
    },
    65: {
        "en": ("Heavy Rain", "🌧️"),
        "bg": ("Силен дъжд", "🌧️")
    },
    66: {
        "en": ("Freezing Rain: Light", "🌨️"),
        "bg": ("Леден дъжд: Слаб", "🌨️")
    },
    67: {
        "en": ("Heavy Freezing Rain", "🌨️"),
        "bg": ("Силен леден дъжд", "🌨️")
    },
    71: {
        "en": ("Snow fall: Slight", "❄️"),
        "bg": ("Снеговалеж: Слаб", "❄️")
    },
    73: {
        "en": ("Snow fall: Moderate", "❄️"),
        "bg": ("Снеговалеж: Умерен", "❄️")
    },
    75: {
        "en": ("Heavy Snow Fall", "❄️"),
        "bg": ("Силен снеговалеж", "❄️")
    },
    77: {
        "en": ("Snow grains", "❄️"),
        "bg": ("Снежни зърна", "❄️")
    },
    80: {
        "en": ("Rain showers: Slight", "🌦️"),
        "bg": ("Превалявания от дъжд: Слаби", "🌦️")
    },
    81: {
        "en": ("Rain showers: Moderate", "🌦️"),
        "bg": ("Превалявания от дъжд: Умерени", "🌦️")
    },
    82: {
        "en": ("Violent Rain Showers", "🌦️"),
        "bg": ("Проливни дъждове", "🌦️")
    },
    85: {
        "en": ("Snow showers: Slight", "🌨️"),
        "bg": ("Превалявания от сняг: Слаби", "🌨️")
    },
    86: {
        "en": ("Heavy Snow Showers", "🌨️"),
        "bg": ("Превалявания от сняг: Силни", "🌨️")
    },
    95: {
        "en": ("Thunderstorm", "⛈️"),
        "bg": ("Гръмотевична буря", "⛈️")
    },
    96: {
        "en": ("Thunderstorm with hail", "⛈️"),
        "bg": ("Гръмотевична буря с градушка", "⛈️")
    },
    99: {
        "en": ("Severe Thunderstorm", "⛈️"),
        "bg": ("Силна гръмотевична буря", "⛈️")
    },
}

DAYS_BG = {
    "Monday": "Понеделник",
    "Tuesday": "Вторник",
    "Wednesday": "Сряда",
    "Thursday": "Четвъртък",
    "Friday": "Петък",
    "Saturday": "Събота",
    "Sunday": "Неделя"
}

DAYS_BG_SHORT = {
    "Mon": "Пон",
    "Tue": "Вт",
    "Wed": "Ср",
    "Thu": "Чет",
    "Fri": "Пет",
    "Sat": "Съб",
    "Sun": "Нед"
}

MONTHS_BG = {
    "January": "Януари",
    "February": "Февруари",
    "March": "Март",
    "April": "Април",
    "May": "Май",
    "June": "Юни",
    "July": "Юли",
    "August": "Август",
    "September": "Септември",
    "October": "Октомври",
    "November": "Ноември",
    "December": "Декември",
    "Jan": "Ян",
    "Feb": "Фев",
    "Mar": "Мар",
    "Apr": "Апр",
    "May": "Май",
    "Jun": "Юни",
    "Jul": "Юли",
    "Aug": "Авг",
    "Sep": "Сеп",
    "Oct": "Окт",
    "Nov": "Ное",
    "Dec": "Дек"
}

TRANSLATIONS = {
    "en": {
        "page_title": "Weather App",
        "city_label": "City",
        "city_placeholder": "Enter city name...",
        "country_label": "Country (Optional)",
        "country_placeholder": "Enter country name...",
        "fetching": "Fetching weather data...",
        "alerts_header": "⚠️ Weather Alerts for {city}",
        "alert_precip": "<strong>Alert for {day_name}:</strong> {condition_name} expected! (<strong>{prob}%</strong> chance of precipitation)",
        "alert_wind": "<strong>Wind Advisory for {day_name}:</strong> High wind speeds expected up to <strong>{wind}</strong>.",
        "alert_rain_soon": "<strong>Heads up:</strong> {condition_name} expected within the hour (<strong>{prob}%</strong> chance of precipitation).",
        "alert_storm_soon": "<strong>Storm Warning:</strong> {condition_name} expected within the hour! (<strong>{prob}%</strong> chance of precipitation)",
        "next_24h": "Immediate Next 24 Hours",
        "show_past_hours": "Show hours that already passed",
        "hourly_unavailable": "Hourly data unavailable.",
        "forecast_7day": "7-Day Forecast",
        "forecast_14day": "14-Day Forecast",
        "live_radar": "Live Radar Nowcast 📡",
        "skywatch_tab": "SkyWatch BG ⚡",
        "btn_24h": "🕐 24h View",
        "hourly_header": "Specific Hourly Forecast for {formatted_date}",
        "hourly_far_future": "Hourly breakdown data is not available this far in the future.",
        "daily_unavailable": "Daily forecast data unavailable.",
        "fetch_failed": "Failed to retrieve weather data. Try a different city.",
        "loc_not_found": "Location not found. Please verify the city and country name.",

        # New Translations Added!
        "lang_label": "Language",
        "open_windy": "🌍 Open Full Radar on Windy.com",
        "open_skywatch": "🌍 Open SkyWatch BG in a New Tab",

        # Card strings
        "card_feels_like": "Feels like",
        "card_day_max": "Day Max",
        "card_day_min": "Day Min",
        "card_hum": "Hum",
        "card_wind": "Wind",
        "card_rain_chance": "Rain chance",
        "severe_weather": "Severe Weather",
        "weather_advisory": "Weather Advisory",
        "unknown": "Unknown",

        # Geolocation strings
        "geo_section_label": "Tap the pin to use your location",
        "geo_divider_text": "or enter manually",
        "geo_success_toast": "📍 Location found: {city}, {country}",
        "geo_header_generic": "Your Current Location",
        "geo_reverse_lookup_failed": "We found your coordinates but couldn't identify the city name. Showing weather for your current location.",

        # Header / theme strings
        "brand_title": "Weather Dashboard",
        "brand_sub": "Live forecast, styled to the season",
        "season_label": "Season",
        "search_button": "Search",

        # Data refresh strings
        "refresh_now_button": "🔄 Refresh now",
        "auto_refresh_label": "Auto-refresh",
        "auto_refresh_help": "Automatically refresh weather data every 15 minutes",
        "last_updated": "Last updated {time}",
    },
    "bg": {
        "page_title": "Приложение за времето",
        "city_label": "Град",
        "city_placeholder": "Въведете име на град...",
        "country_label": "Държава (По избор)",
        "country_placeholder": "Въведете име на държава...",
        "fetching": "Извличане на данни за времето...",
        "alerts_header": "⚠️ Сигнали за времето за {city}",
        "alert_precip": "<strong>Сигнал за {day_name}:</strong> Очаква се {condition_name}! (<strong>{prob}%</strong> шанс за валежи)",
        "alert_wind": "<strong>Предупреждение за вятър за {day_name}:</strong> Очакват се силни ветрове до <strong>{wind}</strong>.",
        "alert_rain_soon": "<strong>Внимание:</strong> Очаква се {condition_name} до един час (<strong>{prob}%</strong> шанс за валежи).",
        "alert_storm_soon": "<strong>Предупреждение за буря:</strong> Очаква се {condition_name} до един час! (<strong>{prob}%</strong> шанс за валежи)",
        "next_24h": "Следващите 24 часа",
        "show_past_hours": "Покажи изминалите часове",
        "hourly_unavailable": "Часовите данни са ненайдостъпни.",
        "forecast_7day": "7-дневна прогноза",
        "forecast_14day": "14-дневна прогноза",
        "live_radar": "Радар на живо 📡",
        "skywatch_tab": "SkyWatch BG ⚡",
        "btn_24h": "🕐 24ч преглед",
        "hourly_header": "Подробна часова прогноза за {formatted_date}",
        "hourly_far_future": "Часовите данни за разпределението не са налични толкова напред във времето.",
        "daily_unavailable": "Данните за ежедневната прогноза са недостъпни.",
        "fetch_failed": "Неуспешно извличане на данни за времето. Опитайте с друг град.",
        "loc_not_found": "Местоположението не е намерено. Моля, проверете името на града и държавата.",

        # New Translations Added!
        "lang_label": "Език",
        "open_windy": "🌍 Отвори пълния радар на Windy.com",
        "open_skywatch": "🌍 Отвори SkyWatch BG в нов таб",

        # Card strings
        "card_feels_like": "Усеща се като",
        "card_day_max": "Макс. за деня",
        "card_day_min": "Мин. за деня",
        "card_hum": "Влаж.",
        "card_wind": "Вятър",
        "card_rain_chance": "Шанс за валежи",
        "severe_weather": "Опасно време",
        "weather_advisory": "Предупреждение за времето",
        "unknown": "Неизвестно",

        # Geolocation strings
        "geo_section_label": "Докоснете иглата за текущото ви местоположение",
        "geo_divider_text": "или потърсете ръчно",
        "geo_success_toast": "📍 Местоположението е намерено: {city}, {country}",
        "geo_header_generic": "Текущото ви местоположение",
        "geo_reverse_lookup_failed": "Намерихме координатите ви, но не успяхме да определим името на града. Показва се времето за текущото ви местоположение.",

        # Header / theme strings
        "brand_title": "Табло за времето",
        "brand_sub": "Прогноза на живо, стилизирана според сезона",
        "season_label": "Сезон",
        "search_button": "Търсене",

        # Data refresh strings
        "refresh_now_button": "🔄 Обнови сега",
        "auto_refresh_label": "Автообновяване",
        "auto_refresh_help": "Автоматично обновяване на данните за времето на всеки 15 минути",
        "last_updated": "Последно обновено {time}",
    }
}

def format_date(date_input: str, format_str: str, lang: str) -> str:
    try:
        # pandas-stubs' to_datetime overloads reference an internal Unknown-typed
        # parameter; the resolved return type here is still the correct Timestamp.
        dt = pd.to_datetime(date_input)  # pyright: ignore[reportUnknownMemberType]
    except Exception:
        return str(date_input)

    # to_datetime doesn't raise for None/"" — it returns NaT, whose strftime() raises.
    if pd.isna(dt):  # pyright: ignore[reportUnknownMemberType]
        return str(date_input)

    if lang == "bg":
        if format_str == "%A, %B %d":
            day_name = DAYS_BG.get(dt.strftime("%A"), dt.strftime("%A"))
            month_name = MONTHS_BG.get(dt.strftime("%B"), dt.strftime("%B"))
            return f"{day_name}, {month_name} {dt.strftime('%d')}"
        elif format_str == "%A, %d %b":
            day_name = DAYS_BG.get(dt.strftime("%A"), dt.strftime("%A"))
            month_name = MONTHS_BG.get(dt.strftime("%b"), dt.strftime("%b"))
            return f"{day_name}, {dt.strftime('%d')} {month_name}"
        elif format_str == "%H:00":
            return dt.strftime("%H:00")
        elif format_str == "%a":
            return DAYS_BG_SHORT.get(dt.strftime("%a"), dt.strftime("%a"))

    return dt.strftime(format_str)

def get_wmo_info(code: int, lang: str = "en") -> tuple[str, str]:
    code_data = WMO_CODES.get(code)
    if code_data and lang in code_data:
        return code_data[lang]
    if code_data and "en" in code_data:
        return code_data["en"]

    default_desc = "Unknown" if lang == "en" else "Неизвестно"
    return (default_desc, "❓")

def format_temperature(value_celsius: float | None, unit: str) -> str:
    """Format a Celsius reading for display, converting to Fahrenheit when requested."""
    if value_celsius is None:
        return f"--°{unit}"
    display_value = value_celsius * 9 / 5 + 32 if unit == "F" else value_celsius
    return f"{round(display_value, 1)}°{unit}"

def format_wind_speed(speed_kmh: float | None, unit: str, lang: str = "en") -> str:
    """Format a km/h wind reading for display, converting to mph when the
    Fahrenheit (imperial) unit is selected so wind stays consistent with temperature."""
    wind_unit = "mph" if unit == "F" else ("km/h" if lang == "en" else "км/ч")
    if speed_kmh is None:
        return f"-- {wind_unit}"
    display_value = speed_kmh * 0.621371 if unit == "F" else speed_kmh
    return f"{round(display_value, 1)} {wind_unit}"

def safe_get(data_dict: dict[str, Any] | None, key: str, idx: int, default: Any = None) -> Any:
    """Safely fetch index from dictionary arrays to prevent IndexErrors on missing API data."""
    if not isinstance(data_dict, dict):
        return default
    arr: Any = data_dict.get(key, [])
    # isinstance narrowing against a bare "list" (no element type available here)
    # resolves to list[Unknown] rather than list[Any]; the values are genuinely
    # untyped JSON data, so this is a stub-precision limit, not a real bug.
    if isinstance(arr, list) and idx < len(arr) and arr[idx] is not None:  # pyright: ignore[reportUnknownArgumentType]
        return arr[idx]  # pyright: ignore[reportUnknownVariableType]
    return default

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

def load_last_location(local_storage: LocalStorage) -> dict[str, str]:
    """Read the last used city/country from the browser's local storage so the search
    fields can be pre-filled on startup. Local storage (not a server-side file) is used
    because this app is hosted for multiple visitors, and each browser must only see its
    own last-used location, not one shared across every visitor."""
    city = local_storage.getItem(LAST_CITY_STORAGE_KEY)
    country = local_storage.getItem(LAST_COUNTRY_STORAGE_KEY)
    return {"city": city or "", "country": country or ""}

def save_last_location(local_storage: LocalStorage, city: str, country: str) -> None:
    """Persist the last used city/country to the browser's local storage so it survives
    app restarts and reloads. Empty values are left untouched rather than overwriting a
    previously remembered location."""
    if city:
        local_storage.setItem(LAST_CITY_STORAGE_KEY, city, key="set_last_city")
    if country:
        local_storage.setItem(LAST_COUNTRY_STORAGE_KEY, country, key="set_last_country")

def load_last_language(local_storage: LocalStorage) -> str | None:
    """Read the last selected UI language from the browser's local storage."""
    return local_storage.getItem(LAST_LANG_STORAGE_KEY)

def save_last_language(local_storage: LocalStorage, lang: str) -> None:
    """Persist the selected UI language to the browser's local storage so it's restored
    on the next visit instead of resetting to English."""
    local_storage.setItem(LAST_LANG_STORAGE_KEY, lang, key="set_last_lang")

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

ALERT_LOOKAHEAD_DAYS = 3

# Near-term (this hour / next hour) rain-vs-storm alert tuning. Open-Meteo's
# hourly array is our finest resolution (no minutely data is fetched), so
# "next 30 min" isn't representable -- this checks the current and next
# hourly slot instead.
NEAR_TERM_LOOKAHEAD_HOURS = 1
NEAR_TERM_RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 66, 80, 81}
# Same severe-weather codes as the daily alert's precip check (65, 67, 75, 82, 86, 95, 96, 99):
# thunderstorms, violent/heavy rain, and heavy snow all warrant the storm-tier alert.
NEAR_TERM_STORM_CODES = {65, 67, 75, 82, 86, 95, 96, 99}
NEAR_TERM_RAIN_PROBABILITY_THRESHOLD = 70

def get_weather_alerts(daily_data: dict[str, Any], lang: str = "en", unit: str = "C") -> list[dict[str, Any]]:
    """Analyze daily data for severe weather or wind alerts, limited to the near term
    (ALERT_LOOKAHEAD_DAYS) since forecasts this far out are unreliable for alerting."""
    alerts: list[dict[str, Any]] = []
    if not daily_data or "time" not in daily_data:
        return alerts

    for i in range(min(len(daily_data["time"]), ALERT_LOOKAHEAD_DAYS)):
        wcode = safe_get(daily_data, "weather_code", i)
        prob = safe_get(daily_data, "precipitation_probability_max", i, 0)
        wind = safe_get(daily_data, "wind_speed_10m_max", i, 0)
        day_name = format_date(daily_data["time"][i], "%A, %B %d", lang)

        if wcode in [65, 67, 75, 82, 86, 95, 96, 99]:
            condition_name = get_wmo_info(wcode, lang)[0]
            msg_tpl = TRANSLATIONS[lang]["alert_precip"]
            alerts.append({
                "severity": "error",
                "message": msg_tpl.format(day_name=day_name, condition_name=condition_name, prob=prob)
            })

        if wind is not None and wind > 50:
            msg_tpl = TRANSLATIONS[lang]["alert_wind"]
            alerts.append({
                "severity": "warning",
                "message": msg_tpl.format(day_name=day_name, wind=format_wind_speed(wind, unit, lang))
            })
    return alerts

def get_near_term_alerts(hourly_data: dict[str, Any], upcoming_start_idx: int, lang: str = "en") -> list[dict[str, Any]]:
    """Check the current and next hourly forecast slot for rain or storm conditions,
    escalating to the storm severity when the worse of the two hours is a thunderstorm
    or heavy/violent precipitation code."""
    if not hourly_data or "time" not in hourly_data:
        return []

    severity_rank: dict[AlertSeverity, int] = {"warning": 1, "error": 2}
    best_rank = 0
    best_severity: AlertSeverity | None = None
    best_code: int | None = None
    best_prob: float | int = 0

    for idx in range(upcoming_start_idx, upcoming_start_idx + NEAR_TERM_LOOKAHEAD_HOURS + 1):
        wcode = safe_get(hourly_data, "weather_code", idx)
        prob = safe_get(hourly_data, "precipitation_probability", idx, 0)

        severity: AlertSeverity
        if wcode in NEAR_TERM_STORM_CODES:
            severity = "error"
        elif wcode in NEAR_TERM_RAIN_CODES or prob >= NEAR_TERM_RAIN_PROBABILITY_THRESHOLD:
            severity = "warning"
        else:
            continue

        # Keep the higher-severity hour; on a tie, keep the sooner one
        # (first match wins) since idx increases with the loop.
        if severity_rank[severity] <= best_rank:
            continue
        best_rank, best_severity, best_code, best_prob = severity_rank[severity], severity, wcode, prob

    if best_severity is None:
        return []

    condition_name = get_wmo_info(best_code if best_code is not None else -1, lang)[0]
    msg_key = "alert_storm_soon" if best_severity == "error" else "alert_rain_soon"
    msg_tpl = TRANSLATIONS[lang][msg_key]
    return [{
        "severity": best_severity,
        "message": msg_tpl.format(condition_name=condition_name, prob=best_prob)
    }]

def generate_forecast_row_html(
    date_str: str,
    code: int | None,
    rain_prob: float | int | str | None,
    wind: float | None,
    max_t: float | None,
    min_t: float | None,
    lang: str = "en",
    unit: str = "C"
) -> str:
    """Generate the HTML for a single compact 14-day forecast table row."""
    try:
        label = format_date(date_str, "%A, %d %b", lang)
    except Exception:
        label = TRANSLATIONS[lang]["unknown"]

    resolved_code = code if code is not None else -1
    desc, emoji = get_wmo_info(resolved_code, lang)
    t = TRANSLATIONS[lang]

    try:
        rain_prob_val = int(rain_prob)  # pyright: ignore[reportArgumentType]
    except (ValueError, TypeError):
        rain_prob_val = 0

    wind_str = format_wind_speed(wind, unit, lang)
    max_t_str = format_temperature(max_t, unit)
    min_t_str = format_temperature(min_t, unit)

    return (
        "<div class='row-14'>"
        f"<div class='day'>{label}</div>"
        f"<div class='emoji' title='{desc}'>{emoji}</div>"
        f"<div class='desc'>{desc}</div>"
        f"<div class='temps'>{max_t_str} <span class='min'>/ {min_t_str}</span></div>"
        f"<div class='rain' title='{t['card_rain_chance']}'>💧 {rain_prob_val}%</div>"
        f"<div class='wind' title='{t['card_wind']}'>💨 {wind_str}</div>"
        "</div>"
    )

def generate_alert_html(message: str, severity: AlertSeverity, lang: str = "en") -> str:
    """Generate the HTML for a single alert banner, matching the design's `.alert` chip.
    Severity ("warning" or "error") picks the icon, tooltip title, and the CSS
    modifier class that makes storm-level alerts read as visibly more urgent."""
    if severity == "error":
        icon = "⛈️"
        title = TRANSLATIONS[lang]["severe_weather"]
    else:
        icon = "⚠️"
        title = TRANSLATIONS[lang]["weather_advisory"]
    return (
        f"<div class='alert alert-{severity}'>"
        f"<span title='{title}'>{icon}</span><span class='text'>{message}</span>"
        "</div>"
    )

def generate_hour_card_html(
    date_str: str,
    code: int | None,
    rain_prob: float | int | str | None,
    temp: float | None,
    lang: str = "en",
    unit: str = "C"
) -> str:
    """Generate the HTML for a single compact 24-hour strip card, matching the design's `.hour-card`."""
    try:
        label = format_date(date_str, "%H:00", lang)
    except Exception:
        label = TRANSLATIONS[lang]["unknown"]

    resolved_code = code if code is not None else -1
    desc, emoji = get_wmo_info(resolved_code, lang)

    try:
        rain_prob_val = int(rain_prob)  # pyright: ignore[reportArgumentType]
    except (ValueError, TypeError):
        rain_prob_val = 0

    temp_str = format_temperature(temp, unit)

    return (
        "<div class='hour-card'>"
        f"<div class='time'>{label}</div>"
        f"<div class='emoji' title='{desc}'>{emoji}</div>"
        f"<div class='temp'>{temp_str}</div>"
        f"<div class='rain'>{rain_prob_val}%</div>"
        "</div>"
    )

def generate_day_card_html(
    date_str: str,
    code: int | None,
    rain_prob: float | int | str | None,
    wind: float | None,
    max_t: float | None,
    min_t: float | None,
    lang: str = "en",
    unit: str = "C"
) -> str:
    """Generate the HTML for a single compact 7-day card, matching the design's `.day-card`."""
    try:
        label = format_date(date_str, "%a", lang)
    except Exception:
        label = TRANSLATIONS[lang]["unknown"]

    resolved_code = code if code is not None else -1
    desc, emoji = get_wmo_info(resolved_code, lang)
    t = TRANSLATIONS[lang]

    try:
        rain_prob_val = int(rain_prob)  # pyright: ignore[reportArgumentType]
    except (ValueError, TypeError):
        rain_prob_val = 0

    wind_str = format_wind_speed(wind, unit, lang)
    max_t_str = format_temperature(max_t, unit)
    min_t_str = format_temperature(min_t, unit)

    return (
        "<div class='day-card'>"
        f"<div class='day'>{label}</div>"
        f"<div class='emoji' title='{desc}'>{emoji}</div>"
        f"<div class='desc'>{desc}</div>"
        f"<div class='temps'>{max_t_str} <span class='min'>/ {min_t_str}</span></div>"
        "<div class='meta'>"
        f"<span title='{t['card_rain_chance']}'>💧 {rain_prob_val}%</span>"
        f"<span title='{t['card_wind']}'>💨 {wind_str}</span>"
        "</div>"
        "</div>"
    )

def get_theme_css(theme: dict[str, str]) -> str:
    """Build the seasonal <link>+<style> block: CSS custom properties from the
    season's palette (see SEASON_THEMES), plus the fixed component styling that
    references them so switching seasons re-skins the whole app."""
    return f"""
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root {{
    --page-bg: {theme['page_bg']};
    --surface: {theme['surface']};
    --border: {theme['border']};
    --text: {theme['text']};
    --accent: {theme['accent']};
    --accent-deep: {theme['accent_deep']};
    --accent-soft: {theme['accent_soft']};
    --accent-grad: {theme['accent_grad']};
    --hero-grad: {theme['hero_grad']};
    --accent-shadow: {theme['accent_shadow']};
    --card-shadow: {theme['card_shadow']};
    --alert-error-bg: color-mix(in srgb, var(--accent-soft) 78%, #c62828 22%);
    --alert-error-border: color-mix(in srgb, var(--accent-deep) 40%, #c62828 60%);
    --alert-error-text: color-mix(in srgb, var(--accent-deep) 55%, #3a0a0a 45%);
    --alert-error-shadow: color-mix(in srgb, var(--accent-shadow) 55%, rgba(198,40,40,.45) 45%);
    --alert-error-shadow-strong: color-mix(in srgb, var(--accent-shadow) 40%, rgba(198,40,40,.6) 60%);
}}

html, [data-testid="stAppViewContainer"], .stApp {{
    background: var(--page-bg) !important;
    font-family: 'Inter', system-ui, sans-serif;
}}
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {{
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    color: var(--text);
}}
/* Hides the top deploy bar completely */
[data-testid="stHeader"] {{ visibility: hidden; display: none; }}

/* ---------- BUTTONS ---------- */
.stButton button[kind="primary"],
[data-testid="stLinkButton"] a[kind="primary"] {{
    background: var(--accent-grad) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    box-shadow: 0 3px 10px var(--accent-shadow) !important;
}}
.stButton button[kind="secondary"] {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}}

/* ---------- TEXT INPUTS ---------- */
[data-testid="stTextInput"] input {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    min-height: 42px;
}}
[data-testid="stTextInput"] label p {{
    font-weight: 700 !important;
    opacity: .7;
}}

/* ---------- SEGMENTED CONTROLS (season swatches, EN/BG, degC/degF pills) ---------- */
[data-testid="stSegmentedControl"] div[role="radiogroup"] {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 3px;
    gap: 2px;
}}
[data-testid="stSegmentedControl"] label {{
    border-radius: 7px !important;
    border: none !important;
    background: transparent !important;
}}
[data-testid="stSegmentedControl"] label p {{
    font-size: 12px !important;
    font-weight: 700 !important;
    color: var(--text) !important;
}}
[data-testid="stSegmentedControl"] label[aria-checked="true"],
[data-testid="stSegmentedControl"] label:has(input:checked) {{
    background: var(--accent-grad) !important;
}}
[data-testid="stSegmentedControl"] label[aria-checked="true"] p,
[data-testid="stSegmentedControl"] label:has(input:checked) p {{
    color: #fff !important;
}}

/* ---------- TABS ---------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
    border-bottom: 1px solid var(--border);
}}
.stTabs [data-baseweb="tab"] {{
    height: auto;
    padding: 10px 18px;
    background: transparent !important;
}}
.stTabs [data-baseweb="tab"] p {{
    font-family: 'Manrope', sans-serif !important;
    font-size: 13.5px !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    opacity: .55;
}}
.stTabs [aria-selected="true"] p {{ opacity: 1; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: var(--accent-deep) !important; }}

/* ---------- ALERTS ---------- */
[data-testid="stAlert"] {{
    border-radius: 12px !important;
    font-weight: 600;
}}
.alert {{ display: flex; align-items: center; gap: 10px; background: var(--accent-soft); border: 1px solid var(--border); border-radius: 12px; padding: 11px 16px; margin-bottom: 8px; }}
.alert .text {{ font-size: 13.5px; font-weight: 600; color: var(--accent-deep); }}
.alert span:first-child {{ cursor: help; }}

/* alert-warning intentionally has no rules of its own -- the base .alert
   styling above is exactly the desired warning-tier look. */
.alert-error {{
    background: var(--alert-error-bg);
    border: 2px solid var(--alert-error-border);
    padding: 10px 16px;
    box-shadow: 0 2px 14px var(--alert-error-shadow);
    animation: alert-pulse 2.6s ease-in-out infinite;
}}
.alert-error .text {{ color: var(--alert-error-text); font-weight: 700; font-size: 14px; }}

@keyframes alert-pulse {{
    0%, 100% {{ box-shadow: 0 2px 14px var(--alert-error-shadow); }}
    50% {{ box-shadow: 0 2px 22px var(--alert-error-shadow-strong); }}
}}
@media (prefers-reduced-motion: reduce) {{
    .alert-error {{ animation: none; }}
}}

/* ---------- APP HEADER ---------- */
.st-key-app_header {{ margin-bottom: 22px; }}
.st-key-app_header [data-testid="stHorizontalBlock"] {{
    align-items: center;
}}
/* Inner control row (season / auto-refresh / language / unit) lives inside col_controls, i.e.
   nested one level deeper than the outer brand/controls split. Let each of its columns shrink
   to fit its actual content instead of stretching to the ratio-based width st.columns() assigns
   by default - that stretching is what left uneven dead-space gaps between the groups. A fixed
   gap on the flex container then gives consistent, tight spacing regardless of content width. */
.st-key-app_header [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] {{
    gap: 22px !important;
    flex-wrap: nowrap;
}}
.st-key-app_header [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    flex: none !important;
    width: auto !important;
    min-width: 0 !important;
}}
.st-key-app_header [data-testid="stCaptionContainer"] {{
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em;
    opacity: .5; color: var(--text); margin-top: 8px; white-space: nowrap;
}}
.st-key-app_header [data-testid="stSegmentedControl"] div[role="radiogroup"] {{
    padding: 2px;
}}
.st-key-app_header [data-testid="stSegmentedControl"] label {{
    padding: 4px 8px !important;
}}
/* Below the mobile breakpoint, stack the control row (season / auto-refresh / language / unit)
   into four rows in DOM order: season alone, refresh alone, then language + unit sharing a row.
   Scoped to .st-key-header_controls (rather than the unlimited-depth descendant selector above)
   so the refresh row's own nested toggle+button columns aren't caught by the same rule. */
@media (max-width: 640px) {{
    .st-key-header_controls {{
        border-top: 1px solid var(--border);
        padding-top: 12px;
        margin-top: 12px;
    }}
    /* Anchored with a direct-child chain (> ... > ...), not an open-ended descendant
       selector, so this only ever matches the season/refresh/lang/unit row itself -
       not the refresh toggle+button row nested several levels deeper inside it,
       which is exactly the ambiguity that made the old rule misbehave. Streamlit
       renders a keyed container's own class on the stVerticalBlock element itself,
       with a stLayoutWrapper as the sole child wrapping the row - verified against
       the live DOM, since this exact chain doesn't otherwise appear elsewhere in
       Streamlit's public docs. */
    .st-key-header_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap !important;
        row-gap: 12px;
    }}
    /* Season swatches (1st column) and the refresh group (2nd column) each break onto
       their own full-width row; language and unit (3rd/4th) are left to share the row
       that remains, splitting it evenly. */
    .st-key-header_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1),
    .st-key-header_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) {{
        flex-basis: 100% !important;
    }}
    .st-key-header_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3),
    .st-key-header_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) {{
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }}

    /* Refresh row: toggle + button side by side on one line, natural width, no stretch.
       Same direct-child chain as above, rooted at .st-key-refresh_group instead - this
       row is already a flex row via Streamlit's own stHorizontalBlock styling, so only
       flex-wrap/gap need overriding, not display. */
    .st-key-refresh_group > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {{
        flex-wrap: nowrap !important;
        align-items: center;
        gap: 8px;
    }}
    .st-key-refresh_group > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
        flex: 0 1 auto;
        min-width: 0;
    }}
    .st-key-refresh_group label p {{
        font-size: 12px;
    }}
    .st-key-refresh_group .stButton button {{
        height: 32px !important;
        min-height: 32px !important;
        padding: 0 10px !important;
        font-size: 11.5px !important;
    }}
}}
.brand-row {{ display: flex; align-items: center; gap: 14px; }}
.brand-icon {{
    width: 44px; height: 44px; border-radius: 12px; background: var(--accent-grad);
    display: flex; align-items: center; justify-content: center; font-size: 22px;
    box-shadow: 0 4px 14px var(--accent-shadow); flex-shrink: 0; cursor: help;
}}
.brand-title {{ font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 21px; letter-spacing: -.01em; color: var(--text); }}
.brand-sub {{ font-size: 12.5px; opacity: .55; font-weight: 500; color: var(--text); }}

/* ---------- SEARCH / LOCATION CARD ---------- */
.st-key-location_card {{
    background: var(--surface);
    border-radius: 16px;
    border: 1px solid var(--border);
    box-shadow: 0 2px 12px var(--card-shadow);
    padding: 20px 22px;
}}
.st-key-location_card [data-testid="stVerticalBlockBorderWrapper"] {{
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    background: transparent !important;
}}
.st-key-search_top [data-testid="stHorizontalBlock"] {{
    align-items: center;
    gap: 14px;
}}
.st-key-search_top [data-testid="stCaptionContainer"] {{
    font-size: 12.5px; font-weight: 400; opacity: .6; color: var(--text);
    text-transform: none; letter-spacing: normal; white-space: nowrap;
}}
.st-key-search_top [data-testid="stCustomComponentV1"] {{
    width: 38px !important; max-width: 38px !important; height: 38px; border-radius: 10px;
    background: var(--accent-soft);
    border: 1px solid var(--border); overflow: hidden;
}}
.location-divider {{ display: flex; align-items: center; gap: 12px; }}
.location-divider-line {{ flex: 1; height: 1px; background: var(--border); }}
.location-divider-text {{ font-size: .78rem; font-weight: 500; opacity: .55; white-space: nowrap; color: var(--text); }}
.st-key-search_action .stButton button {{ margin-top: 27px; }}

/* ---------- LOCATION LINE ---------- */
.location {{ display: flex; align-items: baseline; gap: 8px; margin-bottom: 16px; }}
.location span:first-child {{ cursor: help; }}
.location .name {{ font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 19px; color: var(--text); }}

/* ---------- HERO PANEL ---------- */
.hero {{
    background: var(--hero-grad); border: 1px solid var(--border); border-radius: 18px;
    padding: 26px 28px; box-shadow: 0 4px 20px var(--card-shadow); margin-bottom: 4px;
    display: grid; grid-template-columns: minmax(220px,1fr) 2fr; gap: 24px; align-items: center;
}}
@media (max-width: 760px) {{ .hero {{ grid-template-columns: 1fr; }} }}
.hero-main {{ display: flex; align-items: center; gap: 16px; }}
.hero-emoji {{ font-size: 56px; line-height: 1; cursor: help; }}
.hero-temp {{ font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 44px; line-height: 1; color: var(--text); }}
.hero-feels {{ font-size: 13px; opacity: .65; font-weight: 500; margin-top: 4px; color: var(--text); }}
.hero-desc {{ font-size: 13.5px; font-weight: 700; color: var(--accent-deep); margin-top: 2px; }}
.stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; }}
.stat-chip {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 11px 12px; }}
.stat-chip .label {{ font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; opacity: .5; margin-bottom: 4px; color: var(--text); }}
.stat-chip .value {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 17px; color: var(--text); }}

/* ---------- 24H GRID ---------- */
.hour-strip {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); gap: 10px; }}
.hour-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 12px 10px; text-align: center; }}
.hour-card .time {{ font-size: 11.5px; font-weight: 700; opacity: .6; margin-bottom: 4px; color: var(--text); }}
.hour-card .emoji {{ font-size: 24px; margin-bottom: 2px; cursor: help; }}
.hour-card .temp {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 15px; color: var(--text); }}
.hour-card .rain {{ font-size: 10.5px; opacity: .55; font-weight: 600; margin-top: 2px; color: var(--text); }}

/* ---------- 7-DAY CARDS ---------- */
.day-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }}
.day-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 16px 14px; text-align: center; }}
.day-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px var(--card-shadow); }}
.day-card .day {{ font-size: 12.5px; font-weight: 700; margin-bottom: 6px; color: var(--text); }}
.day-card .emoji {{ font-size: 32px; margin-bottom: 6px; cursor: help; }}
.day-card .desc {{ font-size: 11.5px; font-weight: 600; color: var(--accent-deep); margin-bottom: 10px; min-height: 14px; }}
.day-card .temps {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 15px; color: var(--text); }}
.day-card .temps .min {{ opacity: .45; font-weight: 600; }}
.day-card .meta {{ display: flex; justify-content: center; gap: 10px; font-size: 10.5px; opacity: .55; font-weight: 600; margin-top: 8px; border-top: 1px solid var(--border); padding-top: 8px; color: var(--text); }}
.day-card .meta span {{ cursor: help; }}
.st-key-forecast_tab7 .stButton button {{
    margin-top: 8px; height: 32px !important; min-height: 32px !important; font-size: 11.5px !important;
}}

/* ---------- 14-DAY COMPACT ROWS ---------- */
.st-key-forecast_tab14 {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 14px; overflow: hidden;
}}
.row-14 {{
    display: grid; grid-template-columns: 110px 32px 1fr 90px 70px 80px; align-items: center;
    gap: 12px; padding: 10px 18px; border-bottom: 1px solid var(--border);
}}
.row-14 .day {{ font-size: 12.5px; font-weight: 700; color: var(--text); }}
.row-14 .emoji {{ font-size: 20px; cursor: help; }}
.row-14 .desc {{ font-size: 12.5px; font-weight: 600; opacity: .75; color: var(--text); }}
.row-14 .temps {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 13.5px; text-align: right; color: var(--text); }}
.row-14 .temps .min {{ opacity: .45; font-weight: 600; }}
.row-14 .rain, .row-14 .wind {{ font-size: 11.5px; opacity: .6; font-weight: 600; text-align: right; color: var(--text); cursor: help; }}
.st-key-forecast_tab14 .stButton button {{
    height: 32px !important; min-height: 32px !important; padding: 0 10px !important; font-size: 11.5px !important;
}}
/* The 6 fixed-width grid columns above need ~380px before the flexible 1fr
   column even gets space, which overflows a phone viewport. Below the mobile
   breakpoint, reflow the same six elements into a wrapping flex row instead:
   emoji/day/temps on one line, description on its own line, rain/wind on a third. */
@media (max-width: 640px) {{
    .row-14 {{
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        column-gap: 10px;
        row-gap: 4px;
        padding: 12px 16px;
    }}
    .row-14 .emoji {{ order: 1; }}
    .row-14 .day {{ order: 2; flex: 1 1 auto; min-width: 0; }}
    .row-14 .temps {{ order: 3; }}
    .row-14 .desc {{ order: 4; flex-basis: 100%; text-align: left; }}
    .row-14 .rain {{ order: 5; text-align: left; }}
    .row-14 .wind {{ order: 6; margin-left: auto; }}
}}

/* ---------- RADAR ---------- */
.radar-frame {{ border-radius: 14px; overflow: hidden; border: 1px solid var(--border); box-shadow: 0 4px 16px var(--card-shadow); }}
.radar-frame iframe {{ display: block; width: 100%; height: 560px; border: 0; }}
</style>
"""

def main():
    if "season" not in st.session_state:
        st.session_state.season = "summer"
    if "unit" not in st.session_state:
        st.session_state.unit = "C"
    if "auto_refresh_enabled" not in st.session_state:
        # Off by default: the whole dashboard (including the Radar/SkyWatch iframe
        # embeds) lives in one fragment, so an enabled timer silently reloads those
        # embeds every 15 minutes even with no user interaction. Opt-in avoids that
        # surprise for anyone who never touches the toggle.
        st.session_state.auto_refresh_enabled = False

    current_season = st.session_state.season
    current_unit = st.session_state.unit

    # set_page_config must be the very first Streamlit command, so it can't wait on the
    # local storage read below (which needs a mounted component). Fall back to whatever
    # language guess is already in session state; the local storage read just after fixes
    # session_state.lang itself before any visible content renders, so on a fresh session
    # the only thing that can lag by a run is this literal browser-tab title.
    page_title_lang = st.session_state.get("lang", "en")
    page_title = "Weather App" if page_title_lang == "en" else "Приложение за времето"
    st.set_page_config(page_title=page_title, page_icon="🌤️", layout="wide")

    theme = SEASON_THEMES[current_season]
    st.markdown(get_theme_css(theme), unsafe_allow_html=True)

    local_storage = LocalStorage()
    if "lang" not in st.session_state:
        saved_lang = load_last_language(local_storage)
        st.session_state.lang = saved_lang if saved_lang in TRANSLATIONS else "en"

    # The language switch below calls st.rerun() immediately so the whole page redraws in
    # the new language in one go. Writing to local storage in that same instant would tear
    # the write's component down before the browser applies it, so the write is deferred to
    # this next, rerun-free run instead.
    pending_lang_save = st.session_state.pop("pending_lang_save", None)
    if pending_lang_save:
        save_last_language(local_storage, pending_lang_save)

    current_lang = st.session_state.lang
    t = TRANSLATIONS[current_lang]

    # --- Main Page Header Layout: brand + season swatches + auto-refresh + EN/BG + degC/degF ---
    with st.container(key="app_header"):
        col_brand, col_controls = st.columns([2, 4])

        with col_brand:
            brand_html = (
                "<div class='brand-row'>"
                f"<div class='brand-icon' title='{theme[f'label_{current_lang}']}'>{theme['emoji']}</div>"
                "<div>"
                f"<div class='brand-title'>{t['brand_title']}</div>"
                f"<div class='brand-sub'>{t['brand_sub']}</div>"
                "</div>"
                "</div>"
            )
            st.markdown(brand_html, unsafe_allow_html=True)

        with col_controls, st.container(key="header_controls"):
            col_season, col_refresh, col_lang, col_unit = st.columns(4)

            with col_season:
                season_keys = list(SEASON_THEMES.keys())
                season_legend = t["season_label"] + ": " + " · ".join(
                    f"{SEASON_THEMES[key]['emoji']} {SEASON_THEMES[key][f'label_{current_lang}']}"
                    for key in season_keys
                )
                selected_season = st.segmented_control(
                    label=t["season_label"],
                    options=season_keys,
                    format_func=lambda key: SEASON_THEMES[key]["emoji"],
                    default=current_season,
                    required=True,
                    key="season_selector",
                    label_visibility="collapsed",
                    help=season_legend
                )

            with col_refresh, st.container(key="refresh_group"):
                col_refresh_toggle, col_refresh_button = st.columns(2)
                with col_refresh_toggle:
                    st.session_state.auto_refresh_enabled = st.toggle(
                        t["auto_refresh_label"],
                        value=st.session_state.auto_refresh_enabled,
                        help=t["auto_refresh_help"]
                    )
                with col_refresh_button:
                    # Populated later by the render_weather_dashboard fragment so the
                    # refresh button lives in the header but its click still only
                    # reruns the fragment, not the whole page.
                    refresh_button_slot = st.container()

            with col_lang:
                lang_options = {"EN": "en", "BG": "bg"}
                current_lang_label = "EN" if current_lang == "en" else "BG"
                selected_lang_label = st.segmented_control(
                    label=t["lang_label"],
                    options=list(lang_options.keys()),
                    default=current_lang_label,
                    required=True,
                    key="main_language_selector",
                    label_visibility="collapsed"
                )
                selected_lang = lang_options.get(selected_lang_label, current_lang)

            with col_unit:
                unit_options = {"°C": "C", "°F": "F"}
                current_unit_label = "°C" if current_unit == "C" else "°F"
                selected_unit_label = st.segmented_control(
                    label="Unit",
                    options=list(unit_options.keys()),
                    default=current_unit_label,
                    required=True,
                    key="unit_selector",
                    label_visibility="collapsed"
                )
                selected_unit = unit_options.get(selected_unit_label, current_unit)

    # If any control changed, persist it and rerun so the whole page reflects the new state
    if selected_season != current_season:
        st.session_state.season = selected_season
        st.rerun()
    if selected_lang != current_lang:
        st.session_state.lang = selected_lang
        st.session_state.pending_lang_save = selected_lang
        st.rerun()
    if selected_unit != current_unit:
        st.session_state.unit = selected_unit
        st.rerun()

    lang = st.session_state.lang
    unit = st.session_state.unit
    t = TRANSLATIONS[lang]

    # Initialize session states for specific day drill-down AND remembering user inputs
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None
    if "saved_city" not in st.session_state or "saved_country" not in st.session_state:
        last_location = load_last_location(local_storage)
        st.session_state.saved_city = last_location["city"]
        st.session_state.saved_country = last_location["country"]
    if "location_source" not in st.session_state:
        st.session_state.location_source = "manual"
    if "geo_location" not in st.session_state:
        st.session_state.geo_location = None
    if "geo_processed_coords" not in st.session_state:
        st.session_state.geo_processed_coords = None

    # Input Layout
    with st.container(key="location_card"):
        with st.container(key="search_top"):
            col_geo_icon, col_geo_hint, col_geo_divider = st.columns([1, 3, 5])
            with col_geo_icon:
                geo_result = streamlit_geolocation()
            with col_geo_hint:
                st.caption(t["geo_section_label"])
            with col_geo_divider:
                st.markdown(
                    '<div class="location-divider">'
                    '<span class="location-divider-line"></span>'
                    f'<span class="location-divider-text">{t["geo_divider_text"]}</span>'
                    '<span class="location-divider-line"></span>'
                    '</div>',
                    unsafe_allow_html=True
                )

            geo_lat = geo_result.get("latitude") if geo_result else None
            geo_lon = geo_result.get("longitude") if geo_result else None

            if geo_lat is not None and geo_lon is not None:
                current_coords = (geo_lat, geo_lon)
                # The component keeps returning the same last-known reading on every rerun
                # (it only sends a new value once the user clicks it again), so a plain
                # coordinate comparison is what tells a fresh click apart from that replay.
                is_new_geo_request = current_coords != st.session_state.geo_processed_coords
                if is_new_geo_request:
                    st.session_state.geo_processed_coords = current_coords
                    resolved_location = build_location_from_coordinates(geo_lat, geo_lon, lang)
                    st.session_state.geo_location = resolved_location
                    st.session_state.location_source = "geo"
                    st.session_state.selected_date = None
                    if resolved_location["country"]:
                        st.session_state.saved_city = resolved_location["name"]
                        st.session_state.saved_country = resolved_location["country"]
                        save_last_location(local_storage, resolved_location["name"], resolved_location["country"])
                        st.toast(t["geo_success_toast"].format(
                            city=resolved_location["name"], country=resolved_location["country"]
                        ))
                    else:
                        st.session_state.saved_city = ""
                        st.session_state.saved_country = ""
                    st.rerun()

        c_in1, c_in2, c_in3 = st.columns([1, 1, 1])

        with c_in1:
            city_input = st.text_input(
                t["city_label"],
                value=st.session_state.saved_city,
                placeholder=t["city_placeholder"]
            )
        with c_in2:
            country_input = st.text_input(
                t["country_label"],
                value=st.session_state.saved_country,
                placeholder=t["country_placeholder"]
            )
        with c_in3:
            with st.container(key="search_action"):
                # Streamlit already reruns (and refetches with the current inputs) on any
                # widget interaction, so this button is a visual affordance matching the
                # design rather than a gate the fetch logic below depends on.
                st.button(t["search_button"], type="primary", use_container_width=True, key="search_button")

    # Automatically update our memory state with whatever is currently in the boxes
    # NOTE: geo_processed_coords is intentionally left untouched here. The geolocation
    # component keeps returning the same last-known reading on every rerun (it only
    # sends a new value once the user clicks it again), so clearing this guard would
    # make the app treat that stale reading as "new" on the next rerun and silently
    # snap back to the geolocated city/country, discarding the manual edit.
    if city_input != st.session_state.saved_city:
        st.session_state.saved_city = city_input
        st.session_state.selected_date = None  # Clear selected day when user searches for a new city
        st.session_state.location_source = "manual"
        st.session_state.geo_location = None
        save_last_location(local_storage, st.session_state.saved_city, st.session_state.saved_country)

    if country_input != st.session_state.saved_country:
        st.session_state.saved_country = country_input
        st.session_state.location_source = "manual"
        st.session_state.geo_location = None
        save_last_location(local_storage, st.session_state.saved_city, st.session_state.saved_country)

    # Main Weather Fetching Section
    using_geo_location = (
        st.session_state.location_source == "geo" and st.session_state.geo_location is not None
    )

    # The generic fallback name is language-dependent; keep it in sync with the current UI language.
    active_geo_location = st.session_state.geo_location
    if using_geo_location and active_geo_location is not None and not active_geo_location.get("country"):
        active_geo_location["name"] = t["geo_header_generic"]

    refresh_interval = "15m" if st.session_state.auto_refresh_enabled else None

    @st.fragment(run_every=refresh_interval)
    def render_weather_dashboard(
        location: dict[str, Any],
        lang: str,
        unit: str,
        using_geo_location: bool,
        refresh_button_slot: DeltaGenerator
    ) -> None:
        """Fetch and display current/hourly/daily weather for a resolved location.
        Wrapped in a fragment so the refresh button (rendered into a slot back in
        the header) and the auto-refresh timer only re-run this section, not the
        whole page (search inputs, tabs, scroll, etc.)."""
        t = TRANSLATIONS[lang]

        with refresh_button_slot:
            st.button(t["refresh_now_button"], key="refresh_now_button")
        st.caption(t["last_updated"].format(time=datetime.now().strftime("%H:%M:%S")))

        lat, lon = location["latitude"], location["longitude"]
        with st.spinner(t["fetching"]):
            f_data = get_weather_data(lat, lon)

        if f_data:
            hourly = f_data.get("hourly", {})
            daily = f_data.get("daily", {})
            curr = f_data.get("current", {})

            # Hourly data starts at 00:00 of the current day, so index 0 is
            # usually already in the past by the time the user looks at it.
            # Find the first hour that hasn't happened yet -- this anchors both
            # the near-term rain/storm alert check and the 24h strip below.
            current_time: str | None = curr.get("time")
            current_hour_key = f"{current_time[:13]}:00" if current_time else None
            upcoming_start_idx = 0
            if current_hour_key and hourly and "time" in hourly:
                for idx, time_str in enumerate(hourly["time"]):
                    if time_str >= current_hour_key:
                        upcoming_start_idx = idx
                        break

            # --- Main Screen Location + Hero ---
            # Escaped because this is third-party geocoding/reverse-geocoding data
            # (Open-Meteo / OpenStreetMap Nominatim) rendered via unsafe_allow_html.
            location_label = html.escape(location["name"])
            if location.get("country"):
                location_label += f", {html.escape(location['country'])}"
            st.markdown(
                f"<div class='location'><span title='{t['geo_header_generic']}'>📍</span><span class='name'>{location_label}</span></div>",
                unsafe_allow_html=True
            )

            if using_geo_location and not location.get("country"):
                st.info(t["geo_reverse_lookup_failed"])

            current_code = curr.get("weather_code")
            current_desc, current_emoji = get_wmo_info(
                current_code if current_code is not None else -1, lang
            )
            wind_speed_val = curr.get("wind_speed_10m")
            wind_str = format_wind_speed(wind_speed_val, unit, lang)
            humidity_val = curr.get("relative_humidity_2m")
            humidity_str = f"{humidity_val}%" if humidity_val is not None else "--%"
            rain_chance_val = safe_get(daily, "precipitation_probability_max", 0)
            rain_chance_str = f"{rain_chance_val}%" if rain_chance_val is not None else "--%"

            hero_html = (
                "<div class='hero'>"
                "<div class='hero-main'>"
                f"<div class='hero-emoji' title='{current_desc}'>{current_emoji}</div>"
                "<div>"
                f"<div class='hero-temp'>{format_temperature(curr.get('temperature_2m'), unit)}</div>"
                f"<div class='hero-feels'>{t['card_feels_like']} {format_temperature(curr.get('apparent_temperature'), unit)}</div>"
                f"<div class='hero-desc'>{current_desc}</div>"
                "</div>"
                "</div>"
                "<div class='stat-grid'>"
                f"<div class='stat-chip'><div class='label'>{t['card_day_max']}</div><div class='value'>{format_temperature(safe_get(daily, 'temperature_2m_max', 0), unit)}</div></div>"
                f"<div class='stat-chip'><div class='label'>{t['card_day_min']}</div><div class='value'>{format_temperature(safe_get(daily, 'temperature_2m_min', 0), unit)}</div></div>"
                f"<div class='stat-chip'><div class='label'>{t['card_wind']}</div><div class='value'>{wind_str}</div></div>"
                f"<div class='stat-chip'><div class='label'>{t['card_hum']}</div><div class='value'>{humidity_str}</div></div>"
                f"<div class='stat-chip'><div class='label'>{t['card_rain_chance']}</div><div class='value'>{rain_chance_str}</div></div>"
                "</div>"
                "</div>"
            )
            st.markdown(hero_html, unsafe_allow_html=True)

            # --- Alerts Section (only shown when there's an actual alert) ---
            # Near-term (this hour / next hour) alerts come first since they're
            # the most time-critical, ahead of the multi-day lookahead alerts.
            near_term_alerts = get_near_term_alerts(hourly, upcoming_start_idx, lang=lang) if hourly and "time" in hourly else []
            daily_alerts = get_weather_alerts(daily, lang=lang, unit=unit) if daily and "time" in daily else []
            alerts = near_term_alerts + daily_alerts
            if alerts:
                st.divider()
                st.subheader(t["alerts_header"].format(city=location['name']))
                alerts_html = "".join(
                    generate_alert_html(alert["message"], alert["severity"], lang=lang) for alert in alerts
                )
                st.markdown(alerts_html, unsafe_allow_html=True)

            st.divider()

            # --- Immediate 24h Hourly Track (horizontal scroll strip) ---
            if hourly and "time" in hourly:
                st.subheader(t["next_24h"])

                if "show_past_hours" not in st.session_state:
                    st.session_state.show_past_hours = False
                st.session_state.show_past_hours = st.toggle(
                    t["show_past_hours"], value=st.session_state.show_past_hours
                )

                start_idx = 0 if st.session_state.show_past_hours else upcoming_start_idx
                end_idx = min(start_idx + 24, len(hourly["time"]))
                hour_indices = list(range(start_idx, end_idx))

                hour_cards_html = "".join(
                    generate_hour_card_html(
                        hourly["time"][idx],
                        code=safe_get(hourly, "weather_code", idx),
                        rain_prob=safe_get(hourly, "precipitation_probability", idx),
                        temp=safe_get(hourly, "temperature_2m", idx),
                        lang=lang,
                        unit=unit
                    )
                    for idx in hour_indices
                )
                st.markdown(f"<div class='hour-strip'>{hour_cards_html}</div>", unsafe_allow_html=True)
            else:
                st.warning(t["hourly_unavailable"])

            st.divider()

            # --- Helper function to display card + button (7-day tab) ---
            def display_daily_column(st_col: DeltaGenerator, data_index: int, tab_prefix: str) -> None:
                with st_col:
                    st.markdown(
                        generate_day_card_html(
                            daily["time"][data_index],
                            code=safe_get(daily, "weather_code", data_index),
                            rain_prob=safe_get(daily, "precipitation_probability_max", data_index),
                            wind=safe_get(daily, "wind_speed_10m_max", data_index),
                            max_t=safe_get(daily, "temperature_2m_max", data_index),
                            min_t=safe_get(daily, "temperature_2m_min", data_index),
                            lang=lang,
                            unit=unit
                        ),
                        unsafe_allow_html=True
                    )
                    # UNIQUE KEY: combining the tab name and the date to prevent duplicate key crashes
                    btn_key = f"btn_{tab_prefix}_{daily['time'][data_index]}"
                    if st.button(t["btn_24h"], key=btn_key, use_container_width=True):
                        st.session_state.selected_date = daily["time"][data_index]
                        st.rerun(scope="fragment")

            # --- Long Term Forecasts & Radar Tabs ---
            if daily and "time" in daily:
                tab7, tab14, tab_radar, tab_skywatch = st.tabs(
                    [t["forecast_7day"], t["forecast_14day"], t["live_radar"], t["skywatch_tab"]]
                )

                with tab7:
                    with st.container(key="forecast_tab7"):
                        num_7 = min(7, len(daily["time"]))
                        cols = st.columns(7)
                        for i in range(num_7):
                            display_daily_column(cols[i], i, "tab7")

                with tab14:
                    with st.container(key="forecast_tab14"):
                        num_14 = min(14, len(daily["time"]))
                        for idx in range(num_14):
                            row_col, btn_col = st.columns([6, 1])
                            with row_col:
                                st.markdown(
                                    generate_forecast_row_html(
                                        daily["time"][idx],
                                        code=safe_get(daily, "weather_code", idx),
                                        rain_prob=safe_get(daily, "precipitation_probability_max", idx),
                                        wind=safe_get(daily, "wind_speed_10m_max", idx),
                                        max_t=safe_get(daily, "temperature_2m_max", idx),
                                        min_t=safe_get(daily, "temperature_2m_min", idx),
                                        lang=lang,
                                        unit=unit
                                    ),
                                    unsafe_allow_html=True
                                )
                            with btn_col:
                                btn_key = f"btn_tab14_{daily['time'][idx]}"
                                if st.button(t["btn_24h"], key=btn_key, use_container_width=True):
                                    st.session_state.selected_date = daily["time"][idx]
                                    st.rerun(scope="fragment")

                with tab_radar:
                    st.markdown("<br>", unsafe_allow_html=True)

                    # --- BIG REDIRECT BUTTON TO WINDY.COM ---
                    windy_redirect_url = f"https://www.windy.com/-Weather-radar-radar?radar,{lat},{lon},6"
                    st.link_button(t["open_windy"], url=windy_redirect_url, type="primary")

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Keeps the embedded preview view visible just underneath
                    st.markdown(
                        "<div class='radar-frame'>"
                        f"<iframe src='https://embed.windy.com/embed2.html?lat={lat}&lon={lon}&zoom=6&level=surface&overlay=radar&product=radar&menu=&message=true&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1&play=1' frameborder='0'></iframe>"
                        "</div>",
                        unsafe_allow_html=True
                    )

                with tab_skywatch:
                    st.markdown("<br>", unsafe_allow_html=True)

                    # --- BIG REDIRECT BUTTON TO SKYWATCH BG ---
                    st.link_button(t["open_skywatch"], url=SKYWATCH_URL, type="primary")

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Keeps the embedded preview view visible just underneath
                    st.markdown(
                        "<div class='radar-frame'>"
                        f"<iframe src='{SKYWATCH_URL}' frameborder='0'></iframe>"
                        "</div>",
                        unsafe_allow_html=True
                    )

                # --- Specific Day Clicked Section ---
                if st.session_state.selected_date:
                    st.divider()
                    sel_date = st.session_state.selected_date
                    formatted_sel_date = format_date(sel_date, "%A, %B %d", lang)

                    st.subheader(t["hourly_header"].format(formatted_date=formatted_sel_date))

                    # Find all hour indices that match the clicked date
                    day_indices = [idx for idx, time_str in enumerate(hourly.get("time", [])) if time_str.startswith(sel_date)]

                    if day_indices:
                        day_cards_html = "".join(
                            generate_hour_card_html(
                                hourly["time"][idx],
                                code=safe_get(hourly, "weather_code", idx),
                                rain_prob=safe_get(hourly, "precipitation_probability", idx),
                                temp=safe_get(hourly, "temperature_2m", idx),
                                lang=lang,
                                unit=unit
                            )
                            for idx in day_indices
                        )
                        st.markdown(f"<div class='hour-strip'>{day_cards_html}</div>", unsafe_allow_html=True)
                    else:
                        st.info(t["hourly_far_future"])

            else:
                st.warning(t["daily_unavailable"])
        else:
            st.error(t["fetch_failed"])

    if using_geo_location or city_input:
        with st.spinner(t["fetching"]):
            location = (
                st.session_state.geo_location if using_geo_location
                else get_coordinates(city_input, country_input, lang=lang)
            )

        if location:
            render_weather_dashboard(location, lang, unit, using_geo_location, refresh_button_slot)
        else:
            st.warning(t["loc_not_found"])

if __name__ == "__main__":
    main()
