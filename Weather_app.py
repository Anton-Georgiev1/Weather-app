from typing import Any

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
import httpx
import pandas as pd
from streamlit_geolocation import streamlit_geolocation  # pyright: ignore[reportMissingTypeStubs]

# --- Configuration ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
REVERSE_GEOCODING_API_URL = "https://nominatim.openstreetmap.org/reverse"
REVERSE_GEOCODING_USER_AGENT = "WeatherAppStreamlit/1.0 (+https://github.com/Anton-Georgiev1/Weather-app)"

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
        "app_title": "Weather App Dashboard 🌤️",
        "city_label": "City",
        "city_placeholder": "Enter city name...",
        "country_label": "Country (Optional)",
        "country_placeholder": "Enter country name...",
        "fetching": "Fetching weather data...",
        "current_temp": "Current Temp",
        "real_feel": "Real Feel",
        "max_temp": "Max Temp",
        "min_temp": "Min Temp",
        "wind_speed": "Wind Speed",
        "humidity": "Humidity",
        "rain_chance_today": "Rain Chance Today",
        "alerts_header": "⚠️ Weather Alerts for {city}",
        "no_alerts": "No severe storms or high wind alerts detected for {city} over the next 14 days.",
        "alert_precip": "<strong>Alert for {day_name}:</strong> {condition_name} expected! (<strong>{prob}%</strong> chance of precipitation)",
        "alert_wind": "<strong>Wind Advisory for {day_name}:</strong> High wind speeds expected up to <strong>{wind} km/h</strong>.",
        "next_24h": "Immediate Next 24 Hours",
        "show_past_hours": "Show hours that already passed",
        "hourly_unavailable": "Hourly data unavailable.",
        "forecast_7day": "7-Day Forecast",
        "forecast_14day": "14-Day Forecast",
        "live_radar": "Live Radar Nowcast 📡",
        "btn_24h": "🕐 24h View",
        "hourly_header": "Specific Hourly Forecast for {formatted_date}",
        "hourly_far_future": "Hourly breakdown data is not available this far in the future.",
        "daily_unavailable": "Daily forecast data unavailable.",
        "fetch_failed": "Failed to retrieve weather data. Try a different city.",
        "loc_not_found": "Location not found. Please verify the city and country name.",

        # New Translations Added!
        "lang_label": "Language",
        "open_windy": "🌍 Open Full Radar on Windy.com",

        # Card strings
        "card_current_temp": "Current Temp",
        "card_feels_like": "Feels like",
        "card_day_max": "Day Max",
        "card_day_min": "Day Min",
        "card_max": "Max",
        "card_min": "Min",
        "card_hum": "Hum",
        "card_wind": "Wind",
        "card_rain_chance": "Rain chance",
        "severe_weather": "Severe Weather",
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
    },
    "bg": {
        "page_title": "Приложение за времето",
        "app_title": "Табло за времето 🌤️",
        "city_label": "Град",
        "city_placeholder": "Въведете име на град...",
        "country_label": "Държава (По избор)",
        "country_placeholder": "Въведете име на държава...",
        "fetching": "Извличане на данни за времето...",
        "current_temp": "Текуща темп.",
        "real_feel": "Усеща се като",
        "max_temp": "Макс. темп.",
        "min_temp": "Мин. темп.",
        "wind_speed": "Скорост на вятъра",
        "humidity": "Влажност",
        "rain_chance_today": "Шанс за дъжд днес",
        "alerts_header": "⚠️ Сигнали за времето за {city}",
        "no_alerts": "Не са засечени сигнали за силни бури или силен вятър за {city} през следващите 14 дни.",
        "alert_precip": "<strong>Сигнал за {day_name}:</strong> Очаква се {condition_name}! (<strong>{prob}%</strong> шанс за валежи)",
        "alert_wind": "<strong>Предупреждение за вятър за {day_name}:</strong> Очакват се силни ветрове до <strong>{wind} км/ч</strong>.",
        "next_24h": "Следващите 24 часа",
        "show_past_hours": "Покажи изминалите часове",
        "hourly_unavailable": "Часовите данни са ненайдостъпни.",
        "forecast_7day": "7-дневна прогноза",
        "forecast_14day": "14-дневна прогноза",
        "live_radar": "Радар на живо 📡",
        "btn_24h": "🕐 24ч преглед",
        "hourly_header": "Подробна часова прогноза за {formatted_date}",
        "hourly_far_future": "Часовите данни за разпределението не са налични толкова напред във времето.",
        "daily_unavailable": "Данните за ежедневната прогноза са недостъпни.",
        "fetch_failed": "Неуспешно извличане на данни за времето. Опитайте с друг град.",
        "loc_not_found": "Местоположението не е намерено. Моля, проверете името на града и държавата.",

        # New Translations Added!
        "lang_label": "Език",
        "open_windy": "🌍 Отвори пълния радар на Windy.com",

        # Card strings
        "card_current_temp": "Текуща темп.",
        "card_feels_like": "Усеща се като",
        "card_day_max": "Макс. за деня",
        "card_day_min": "Мин. за деня",
        "card_max": "Макс",
        "card_min": "Мин",
        "card_hum": "Влаж.",
        "card_wind": "Вятър",
        "card_rain_chance": "Шанс за валежи",
        "severe_weather": "Опасно време",
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
    }
}

def format_date(date_input: str, format_str: str, lang: str) -> str:
    try:
        # pandas-stubs' to_datetime overloads reference an internal Unknown-typed
        # parameter; the resolved return type here is still the correct Timestamp.
        dt = pd.to_datetime(date_input)  # pyright: ignore[reportUnknownMemberType]
    except Exception:
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
        if not name or not country:
            return None
        return {"name": name, "country": country}
    except Exception:
        return None

def build_location_from_coordinates(lat: float, lon: float, lang: str = "en") -> dict[str, Any]:
    """Build a location dict (matching get_coordinates' shape) directly from browser-provided coordinates."""
    resolved = reverse_geocode(lat, lon, lang)
    if resolved:
        return {"name": resolved["name"], "country": resolved["country"], "latitude": lat, "longitude": lon}
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

def calculate_daily_average_humidity(hourly_hum_data: list[float | None]) -> list[float | None]:
    """Calculate daily average humidity from hourly data (24-hour chunks)."""
    daily_hum_list: list[float | None] = []
    if not hourly_hum_data:
        return []
    for i in range(0, len(hourly_hum_data), 24):
        chunk = [x for x in hourly_hum_data[i:i+24] if x is not None]
        daily_hum_list.append(sum(chunk) / len(chunk) if chunk else None)
    return daily_hum_list

def get_weather_alerts(daily_data: dict[str, Any], lang: str = "en") -> list[dict[str, Any]]:
    """Analyze daily data for severe weather or wind alerts."""
    alerts: list[dict[str, Any]] = []
    if not daily_data or "time" not in daily_data:
        return alerts

    for i in range(len(daily_data["time"])):
        wcode = safe_get(daily_data, "weather_code", i)
        prob = safe_get(daily_data, "precipitation_probability_max", i, 0)
        wind = safe_get(daily_data, "wind_speed_10m_max", i, 0)
        day_name = format_date(daily_data["time"][i], "%A, %B %d", lang)

        if wcode in [65, 67, 75, 82, 86, 95, 96, 99]:
            condition_name = get_wmo_info(wcode, lang)[0]
            msg_tpl = TRANSLATIONS[lang]["alert_precip"]
            alerts.append({
                "type": "error",
                "message": msg_tpl.format(day_name=day_name, condition_name=condition_name, prob=prob)
            })

        if wind is not None and wind > 50:
            msg_tpl = TRANSLATIONS[lang]["alert_wind"]
            alerts.append({
                "type": "warning",
                "message": msg_tpl.format(day_name=day_name, wind=wind)
            })
    return alerts

def generate_forecast_card_html(
    date_str: str,
    code: int | None,
    rain_prob: float | int | str | None,
    wind: float | None = None,
    humidity: float | None = None,
    max_t: float | None = None,
    min_t: float | None = None,
    app_max: float | None = None,
    app_min: float | None = None,
    hour_t: float | None = None,
    hour_app: float | None = None,
    is_hourly: bool = False,
    lang: str = "en",
    unit: str = "C"
) -> str:
    """Generate the HTML for a forecast card."""
    try:
        label = format_date(date_str, "%H:00" if is_hourly else "%A, %d %b", lang)
    except Exception:
        label = TRANSLATIONS[lang]["unknown"]

    resolved_code = code if code is not None else -1
    desc, emoji = get_wmo_info(resolved_code, lang)

    desc_class = ""
    if resolved_code == 96:
        desc_class = "desc-hail"
    elif resolved_code in [95, 99]:
        desc_class = "desc-thunderstorm"

    try:
        rain_prob_val = int(rain_prob)  # pyright: ignore[reportArgumentType]
    except (ValueError, TypeError):
        rain_prob_val = 0

    card_bg_class = "rain-bg" if rain_prob_val > 30 else ""
    rain_text_class = "high-prob" if rain_prob_val > 20 else ""

    t = TRANSLATIONS[lang]

    wind_unit = "km/h" if lang == "en" else "км/ч"
    wind_str = f"{round(wind, 1)} {wind_unit}" if wind is not None else f"-- {wind_unit}"
    humidity_str = f"{int(humidity)}%" if humidity is not None else "--%"
    max_t_str = format_temperature(max_t, unit)
    min_t_str = format_temperature(min_t, unit)

    if is_hourly:
        hour_t_str = format_temperature(hour_t, unit)
        hour_app_str = format_temperature(hour_app, unit)
        temp_html = (
            f"<div class='temp-primary'>{t['card_current_temp']}: {hour_t_str}</div>"
            f"<div class='temp-secondary mb-small'>{t['card_feels_like']} {hour_app_str}</div>"
            f"<div class='temp-tertiary'>{t['card_day_max']}: {max_t_str}</div>"
            f"<div class='temp-tertiary mb-small'>{t['card_day_min']}: {min_t_str}</div>"
        )
    else:
        app_max_str = format_temperature(app_max, unit)
        app_min_str = format_temperature(app_min, unit)
        temp_html = (
            f"<div class='temp-primary'>{t['card_max']}: {max_t_str}</div>"
            f"<div class='temp-secondary'>{t['card_feels_like']} {app_max_str}</div>"
            f"<div class='temp-primary mt-small'>{t['card_min']}: {min_t_str}</div>"
            f"<div class='temp-secondary mb-small'>{t['card_feels_like']} {app_min_str}</div>"
        )

    return (
        f"<div class='forecast-card {card_bg_class}'>"
        f"<div class='forecast-time'>{label}</div>"
        f"<div class='forecast-emoji'>{emoji}</div>"
        f"<div class='forecast-desc {desc_class}'>{desc}</div>"
        f"{temp_html}"
        f"<div class='forecast-divider'>"
        f"<div class='forecast-extra'>{t['card_hum']}: {humidity_str}</div>"
        f"<div class='forecast-extra'>{t['card_wind']}: {wind_str}</div>"
        f"<div class='forecast-rain {rain_text_class}'>{t['card_rain_chance']}: {rain_prob_val}%</div>"
        f"</div>"
        f"</div>"
    )

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

    try:
        rain_prob_val = int(rain_prob)  # pyright: ignore[reportArgumentType]
    except (ValueError, TypeError):
        rain_prob_val = 0

    wind_unit = "km/h" if lang == "en" else "км/ч"
    wind_str = f"{round(wind, 1)} {wind_unit}" if wind is not None else f"-- {wind_unit}"
    max_t_str = format_temperature(max_t, unit)
    min_t_str = format_temperature(min_t, unit)

    return (
        "<div class='row-14'>"
        f"<div class='day'>{label}</div>"
        f"<div class='emoji'>{emoji}</div>"
        f"<div class='desc'>{desc}</div>"
        f"<div class='temps'>{max_t_str} <span class='min'>/ {min_t_str}</span></div>"
        f"<div class='rain'>💧 {rain_prob_val}%</div>"
        f"<div class='wind'>💨 {wind_str}</div>"
        "</div>"
    )

def generate_alert_html(icon: str, message: str) -> str:
    """Generate the HTML for a single alert banner, matching the design's `.alert` chip."""
    return f"<div class='alert'><span>{icon}</span><span class='text'>{message}</span></div>"

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
    _desc, emoji = get_wmo_info(resolved_code, lang)

    try:
        rain_prob_val = int(rain_prob)  # pyright: ignore[reportArgumentType]
    except (ValueError, TypeError):
        rain_prob_val = 0

    temp_str = format_temperature(temp, unit)

    return (
        "<div class='hour-card'>"
        f"<div class='time'>{label}</div>"
        f"<div class='emoji'>{emoji}</div>"
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

    try:
        rain_prob_val = int(rain_prob)  # pyright: ignore[reportArgumentType]
    except (ValueError, TypeError):
        rain_prob_val = 0

    wind_val = round(wind) if wind is not None else "--"
    max_t_str = format_temperature(max_t, unit)
    min_t_str = format_temperature(min_t, unit)

    return (
        "<div class='day-card'>"
        f"<div class='day'>{label}</div>"
        f"<div class='emoji'>{emoji}</div>"
        f"<div class='desc'>{desc}</div>"
        f"<div class='temps'>{max_t_str} <span class='min'>/ {min_t_str}</span></div>"
        "<div class='meta'>"
        f"<span>💧 {rain_prob_val}%</span>"
        f"<span>💨 {wind_val}</span>"
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

/* ---------- APP HEADER ---------- */
.st-key-app_header {{ margin-bottom: 22px; }}
.st-key-app_header [data-testid="stHorizontalBlock"] {{
    align-items: center;
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
.brand-row {{ display: flex; align-items: center; gap: 14px; }}
.brand-icon {{
    width: 44px; height: 44px; border-radius: 12px; background: var(--accent-grad);
    display: flex; align-items: center; justify-content: center; font-size: 22px;
    box-shadow: 0 4px 14px var(--accent-shadow); flex-shrink: 0;
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
.location .name {{ font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 19px; color: var(--text); }}

/* ---------- HERO PANEL ---------- */
.hero {{
    background: var(--hero-grad); border: 1px solid var(--border); border-radius: 18px;
    padding: 26px 28px; box-shadow: 0 4px 20px var(--card-shadow); margin-bottom: 4px;
    display: grid; grid-template-columns: minmax(220px,1fr) 2fr; gap: 24px; align-items: center;
}}
@media (max-width: 760px) {{ .hero {{ grid-template-columns: 1fr; }} }}
.hero-main {{ display: flex; align-items: center; gap: 16px; }}
.hero-emoji {{ font-size: 56px; line-height: 1; }}
.hero-temp {{ font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 44px; line-height: 1; color: var(--text); }}
.hero-feels {{ font-size: 13px; opacity: .65; font-weight: 500; margin-top: 4px; color: var(--text); }}
.hero-desc {{ font-size: 13.5px; font-weight: 700; color: var(--accent-deep); margin-top: 2px; }}
.stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; }}
.stat-chip {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 11px 12px; }}
.stat-chip .label {{ font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; opacity: .5; margin-bottom: 4px; color: var(--text); }}
.stat-chip .value {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 17px; color: var(--text); }}

/* ---------- 24H STRIP ---------- */
.hour-strip {{ display: flex; gap: 10px; overflow-x: auto; padding-bottom: 6px; }}
.hour-card {{ min-width: 96px; flex-shrink: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 12px 10px; text-align: center; }}
.hour-card .time {{ font-size: 11.5px; font-weight: 700; opacity: .6; margin-bottom: 4px; color: var(--text); }}
.hour-card .emoji {{ font-size: 24px; margin-bottom: 2px; }}
.hour-card .temp {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 15px; color: var(--text); }}
.hour-card .rain {{ font-size: 10.5px; opacity: .55; font-weight: 600; margin-top: 2px; color: var(--text); }}

/* ---------- 7-DAY CARDS ---------- */
.day-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }}
.day-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 16px 14px; text-align: center; }}
.day-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px var(--card-shadow); }}
.day-card .day {{ font-size: 12.5px; font-weight: 700; margin-bottom: 6px; color: var(--text); }}
.day-card .emoji {{ font-size: 32px; margin-bottom: 6px; }}
.day-card .desc {{ font-size: 11.5px; font-weight: 600; color: var(--accent-deep); margin-bottom: 10px; min-height: 14px; }}
.day-card .temps {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 15px; color: var(--text); }}
.day-card .temps .min {{ opacity: .45; font-weight: 600; }}
.day-card .meta {{ display: flex; justify-content: center; gap: 10px; font-size: 10.5px; opacity: .55; font-weight: 600; margin-top: 8px; border-top: 1px solid var(--border); padding-top: 8px; color: var(--text); }}
.st-key-forecast_tab7 .stButton button {{
    margin-top: 8px; height: 32px !important; min-height: 32px !important; font-size: 11.5px !important;
}}

/* ---------- CUSTOM FORECAST CARD ---------- */
.forecast-card {{
    text-align: center; padding: 16px 14px; border-radius: 14px;
    border: 1px solid var(--border); background: var(--surface);
    margin: 6px 0; box-shadow: 0 2px 10px var(--card-shadow);
    transition: transform .15s ease, box-shadow .15s ease;
}}
.forecast-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px var(--card-shadow); }}
.forecast-card.rain-bg {{ background: var(--accent-soft); }}
.forecast-time {{ font-weight: 700; font-size: 1.05em; margin-bottom: 5px; color: var(--text); }}
.forecast-emoji {{ font-size: 2.6em; line-height: 1.2; margin-bottom: 0; }}
.forecast-desc {{ font-size: .95em; font-weight: 700; color: var(--accent-deep); margin-bottom: 10px; }}
.forecast-desc.desc-thunderstorm {{ color: #b8860b; }}
.forecast-desc.desc-hail {{ color: #b5432b; }}
.temp-primary {{ font-size: 1.05em; font-weight: 700; color: var(--text); }}
.temp-secondary {{ font-size: .82em; opacity: .7; color: var(--text); }}
.temp-tertiary {{ font-size: .88em; font-weight: 600; opacity: .85; color: var(--text); }}
.mt-small {{ margin-top: 8px; }}
.mb-small {{ margin-bottom: 8px; }}
.forecast-divider {{ margin-top: 10px; border-top: 1px solid var(--border); padding-top: 8px; }}
.forecast-extra {{ font-size: .82em; opacity: .7; color: var(--text); }}
.forecast-rain {{ font-size: .92em; font-weight: 600; margin-top: 8px; color: var(--text); }}
.forecast-rain.high-prob {{ color: var(--accent-deep); }}

/* ---------- 14-DAY COMPACT ROWS ---------- */
.st-key-forecast_tab14 {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 14px; overflow: hidden;
}}
.row-14 {{
    display: grid; grid-template-columns: 110px 32px 1fr 90px 70px 80px; align-items: center;
    gap: 12px; padding: 10px 18px; border-bottom: 1px solid var(--border);
}}
.row-14 .day {{ font-size: 12.5px; font-weight: 700; color: var(--text); }}
.row-14 .emoji {{ font-size: 20px; }}
.row-14 .desc {{ font-size: 12.5px; font-weight: 600; opacity: .75; color: var(--text); }}
.row-14 .temps {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 13.5px; text-align: right; color: var(--text); }}
.row-14 .temps .min {{ opacity: .45; font-weight: 600; }}
.row-14 .rain, .row-14 .wind {{ font-size: 11.5px; opacity: .6; font-weight: 600; text-align: right; color: var(--text); }}
.st-key-forecast_tab14 .stButton button {{
    height: 32px !important; min-height: 32px !important; padding: 0 10px !important; font-size: 11.5px !important;
}}

/* ---------- RADAR ---------- */
.radar-frame {{ border-radius: 14px; overflow: hidden; border: 1px solid var(--border); box-shadow: 0 4px 16px var(--card-shadow); }}
.radar-frame iframe {{ display: block; width: 100%; height: 560px; border: 0; }}
</style>
"""

def main():
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "season" not in st.session_state:
        st.session_state.season = "summer"
    if "unit" not in st.session_state:
        st.session_state.unit = "C"

    current_lang = st.session_state.lang
    current_season = st.session_state.season
    current_unit = st.session_state.unit

    page_title = "Weather App" if current_lang == "en" else "Приложение за времето"
    st.set_page_config(page_title=page_title, page_icon="🌤️", layout="wide")

    theme = SEASON_THEMES[current_season]
    st.markdown(get_theme_css(theme), unsafe_allow_html=True)

    t = TRANSLATIONS[current_lang]

    # --- Main Page Header Layout: brand + season swatches + EN/BG + degC/degF ---
    with st.container(key="app_header"):
        col_brand, col_controls = st.columns([3, 3])

        with col_brand:
            brand_html = (
                "<div class='brand-row'>"
                f"<div class='brand-icon'>{theme['emoji']}</div>"
                "<div>"
                f"<div class='brand-title'>{t['brand_title']}</div>"
                f"<div class='brand-sub'>{t['brand_sub']}</div>"
                "</div>"
                "</div>"
            )
            st.markdown(brand_html, unsafe_allow_html=True)

        with col_controls:
            col_season_label, col_season_swatches, col_lang, col_unit = st.columns([1, 2, 1, 1])

            with col_season_label:
                st.caption(t["season_label"])

            with col_season_swatches:
                season_keys = list(SEASON_THEMES.keys())
                selected_season = st.segmented_control(
                    label=t["season_label"],
                    options=season_keys,
                    format_func=lambda key: SEASON_THEMES[key]["emoji"],
                    default=current_season,
                    required=True,
                    key="season_selector",
                    label_visibility="collapsed"
                )

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
    if "saved_city" not in st.session_state:
        st.session_state.saved_city = ""
    if "saved_country" not in st.session_state:
        st.session_state.saved_country = ""
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
                # The component keeps returning the same last-known reading on every rerun, so
                # also re-trigger when the user has since switched to manual entry (location_source
                # != "geo") even if the browser hands back identical coordinates as before.
                is_new_geo_request = (
                    current_coords != st.session_state.geo_processed_coords
                    or st.session_state.location_source != "geo"
                )
                if is_new_geo_request:
                    st.session_state.geo_processed_coords = current_coords
                    resolved_location = build_location_from_coordinates(geo_lat, geo_lon, lang)
                    st.session_state.geo_location = resolved_location
                    st.session_state.location_source = "geo"
                    st.session_state.selected_date = None
                    if resolved_location["country"]:
                        st.session_state.saved_city = resolved_location["name"]
                        st.session_state.saved_country = resolved_location["country"]
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

    if country_input != st.session_state.saved_country:
        st.session_state.saved_country = country_input
        st.session_state.location_source = "manual"
        st.session_state.geo_location = None

    # Main Weather Fetching Section
    using_geo_location = (
        st.session_state.location_source == "geo" and st.session_state.geo_location is not None
    )

    # The generic fallback name is language-dependent; keep it in sync with the current UI language.
    active_geo_location = st.session_state.geo_location
    if using_geo_location and active_geo_location is not None and not active_geo_location.get("country"):
        active_geo_location["name"] = t["geo_header_generic"]

    if using_geo_location or city_input:
        with st.spinner(t["fetching"]):
            location = (
                st.session_state.geo_location if using_geo_location
                else get_coordinates(city_input, country_input, lang=lang)
            )

            if location:
                lat, lon = location["latitude"], location["longitude"]
                f_data = get_weather_data(lat, lon)

                if f_data:
                    hourly = f_data.get("hourly", {})
                    daily = f_data.get("daily", {})
                    curr = f_data.get("current", {})

                    # --- Main Screen Location + Hero ---
                    location_label = location["name"]
                    if location.get("country"):
                        location_label += f", {location['country']}"
                    st.markdown(
                        f"<div class='location'><span>📍</span><span class='name'>{location_label}</span></div>",
                        unsafe_allow_html=True
                    )

                    if using_geo_location and not location.get("country"):
                        st.info(t["geo_reverse_lookup_failed"])

                    current_code = curr.get("weather_code")
                    current_desc, current_emoji = get_wmo_info(
                        current_code if current_code is not None else -1, lang
                    )
                    wind_unit = "km/h" if lang == "en" else "км/ч"
                    wind_speed_val = curr.get("wind_speed_10m")
                    wind_str = f"{wind_speed_val} {wind_unit}" if wind_speed_val is not None else f"-- {wind_unit}"
                    humidity_val = curr.get("relative_humidity_2m")
                    humidity_str = f"{humidity_val}%" if humidity_val is not None else "--%"
                    rain_chance_val = safe_get(daily, "precipitation_probability_max", 0)
                    rain_chance_str = f"{rain_chance_val}%" if rain_chance_val is not None else "--%"

                    hero_html = (
                        "<div class='hero'>"
                        "<div class='hero-main'>"
                        f"<div class='hero-emoji'>{current_emoji}</div>"
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

                    st.divider()

                    # --- Alerts Section ---
                    if daily and "time" in daily:
                        st.subheader(t["alerts_header"].format(city=location['name']))
                        alerts = get_weather_alerts(daily, lang=lang)

                        if alerts:
                            alerts_html = "".join(generate_alert_html("⚠️", alert["message"]) for alert in alerts)
                            st.markdown(alerts_html, unsafe_allow_html=True)
                        else:
                            st.markdown(
                                generate_alert_html("✅", t["no_alerts"].format(city=location['name'])),
                                unsafe_allow_html=True
                            )

                    st.divider()

                    # --- Immediate 24h Hourly Track (horizontal scroll strip) ---
                    if hourly and "time" in hourly:
                        st.subheader(t["next_24h"])

                        # Hourly data starts at 00:00 of the current day, so index 0 is
                        # usually already in the past by the time the user looks at it.
                        # Find the first hour that hasn't happened yet and default the
                        # window to start there instead of showing stale hours first.
                        current_time: str | None = curr.get("time")
                        current_hour_key = f"{current_time[:13]}:00" if current_time else None
                        upcoming_start_idx = 0
                        if current_hour_key:
                            for idx, time_str in enumerate(hourly["time"]):
                                if time_str >= current_hour_key:
                                    upcoming_start_idx = idx
                                    break

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
                                st.rerun()

                    # --- Long Term Forecasts & Radar Tabs ---
                    if daily and "time" in daily:
                        tab7, tab14, tab_radar = st.tabs([t["forecast_7day"], t["forecast_14day"], t["live_radar"]])

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
                                            st.rerun()

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
            else:
                st.warning(t["loc_not_found"])

if __name__ == "__main__":
    main()
