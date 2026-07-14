import streamlit as st
import httpx
import pandas as pd
from streamlit_geolocation import streamlit_geolocation

# --- Configuration ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
REVERSE_GEOCODING_API_URL = "https://nominatim.openstreetmap.org/reverse"
REVERSE_GEOCODING_USER_AGENT = "WeatherAppStreamlit/1.0 (+https://github.com/Anton-Georgiev1/Weather-app)"

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
        "alerts_header": "⚠️ Weather Alerts for {city}",
        "no_alerts": "No severe storms or high wind alerts detected for {city} over the next 14 days.",
        "alert_precip": "**Alert for {day_name}:** {condition_name} expected! (**{prob}%** chance of precipitation)",
        "alert_wind": "**Wind Advisory for {day_name}:** High wind speeds expected up to **{wind} km/h**.",
        "next_24h": "Immediate Next 24 Hours",
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
        "geo_section_label": "📍 Use your current location",
        "geo_permission_hint": "Your browser may ask permission to share your location.",
        "geo_divider_text": "or enter manually",
        "geo_success_toast": "📍 Location found: {city}, {country}",
        "geo_header_generic": "Your Current Location",
        "geo_reverse_lookup_failed": "We found your coordinates but couldn't identify the city name. Showing weather for your current location."
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
        "alerts_header": "⚠️ Сигнали за времето за {city}",
        "no_alerts": "Не са засечени сигнали за силни бури или силен вятър за {city} през следващите 14 дни.",
        "alert_precip": "**Сигнал за {day_name}:** Очаква се {condition_name}! (**{prob}%** шанс за валежи)",
        "alert_wind": "**Предупреждение за вятър за {day_name}:** Очакват се силни ветрове до **{wind} км/ч**.",
        "next_24h": "Следващите 24 часа",
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
        "geo_section_label": "📍 Използвайте текущото си местоположение",
        "geo_permission_hint": "Браузърът може да поиска разрешение за споделяне на местоположението ви.",
        "geo_divider_text": "или потърсете ръчно",
        "geo_success_toast": "📍 Местоположението е намерено: {city}, {country}",
        "geo_header_generic": "Текущото ви местоположение",
        "geo_reverse_lookup_failed": "Намерихме координатите ви, но не успяхме да определим името на града. Показва се времето за текущото ви местоположение."
    }
}

def format_date(date_input, format_str: str, lang: str) -> str:
    try:
        dt = pd.to_datetime(date_input)
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
            
    return dt.strftime(format_str)

def get_wmo_info(code, lang="en"):
    code_data = WMO_CODES.get(code)
    if code_data and lang in code_data:
        return code_data[lang]
    if code_data and "en" in code_data:
        return code_data["en"]
    
    default_desc = "Unknown" if lang == "en" else "Неизвестно"
    return (default_desc, "❓")

def safe_get(data_dict, key, idx, default=None):
    """Safely fetch index from dictionary arrays to prevent IndexErrors on missing API data."""
    if not isinstance(data_dict, dict):
        return default
    arr = data_dict.get(key, [])
    if isinstance(arr, list) and idx < len(arr) and arr[idx] is not None:
        return arr[idx]
    return default

def get_coordinates(city: str, country: str | None = None) -> dict | None:
    query = city.strip()
    if not query: return None
    if country and country.strip(): query += f", {country.strip()}"
    params = {"name": query, "count": 1, "language": "en", "format": "json"}
    try:
        response = httpx.get(GEOCODING_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["results"][0] if "results" in data and data["results"] else None
    except Exception:
        return None

def reverse_geocode(lat: float, lon: float, lang: str = "en") -> dict | None:
    """Resolve a display name and country for coordinates via OpenStreetMap Nominatim."""
    params = {"lat": lat, "lon": lon, "format": "jsonv2", "accept-language": lang}
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

def build_location_from_coordinates(lat: float, lon: float, lang: str = "en") -> dict:
    """Build a location dict (matching get_coordinates' shape) directly from browser-provided coordinates."""
    resolved = reverse_geocode(lat, lon, lang)
    if resolved:
        return {"name": resolved["name"], "country": resolved["country"], "latitude": lat, "longitude": lon}
    return {"name": TRANSLATIONS[lang]["geo_header_generic"], "country": "", "latitude": lat, "longitude": lon}

def get_weather_data(lat: float, lon: float):
    f_params = {
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
    daily_hum_list = []
    if not hourly_hum_data:
        return []
    for i in range(0, len(hourly_hum_data), 24):
        chunk = [x for x in hourly_hum_data[i:i+24] if x is not None]
        daily_hum_list.append(sum(chunk) / len(chunk) if chunk else None)
    return daily_hum_list

def get_weather_alerts(daily_data: dict, lang: str = "en") -> list[dict]:
    """Analyze daily data for severe weather or wind alerts."""
    alerts = []
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

def generate_forecast_card_html(date_str, code, rain_prob, wind=None, humidity=None, 
                               max_t=None, min_t=None, app_max=None, app_min=None, 
                               hour_t=None, hour_app=None, is_hourly=False, lang="en") -> str:
    """Generate the HTML for a forecast card."""
    try:
        label = format_date(date_str, "%H:00" if is_hourly else "%A, %d %b", lang)
    except Exception:
        label = TRANSLATIONS[lang]["unknown"]
    
    code = code if code is not None else -1
    desc, emoji = get_wmo_info(code, lang)
    
    desc_class = ""
    if code == 96:
        desc_class = "desc-hail"
    elif code in [95, 99]:
        desc_class = "desc-thunderstorm"

    try:
        rain_prob_val = int(rain_prob)
    except (ValueError, TypeError):
        rain_prob_val = 0
        
    card_bg_class = "rain-bg" if rain_prob_val > 30 else ""
    rain_text_class = "high-prob" if rain_prob_val > 20 else ""
    
    t = TRANSLATIONS[lang]
    
    wind_unit = "km/h" if lang == "en" else "км/ч"
    wind_str = f"{round(wind, 1)} {wind_unit}" if wind is not None else f"-- {wind_unit}"
    humidity_str = f"{int(humidity)}%" if humidity is not None else "--%"
    max_t_str = f"{round(max_t, 1)}°" if max_t is not None else "--°"
    min_t_str = f"{round(min_t, 1)}°" if min_t is not None else "--°"
    
    if is_hourly:
        hour_t_str = f"{round(hour_t, 1)}°" if hour_t is not None else "--°"
        hour_app_str = f"{round(hour_app, 1)}°" if hour_app is not None else "--°"
        temp_html = (
            f"<div class='temp-primary'>{t['card_current_temp']}: {hour_t_str}</div>"
            f"<div class='temp-secondary mb-small'>{t['card_feels_like']} {hour_app_str}</div>"
            f"<div class='temp-tertiary'>{t['card_day_max']}: {max_t_str}</div>"
            f"<div class='temp-tertiary mb-small'>{t['card_day_min']}: {min_t_str}</div>"
        )
    else:
        app_max_str = f"{round(app_max, 1)}°" if app_max is not None else "--°"
        app_min_str = f"{round(app_min, 1)}°" if app_min is not None else "--°"
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

def render_forecast_card(*args, **kwargs):
    html_content = generate_forecast_card_html(*args, **kwargs)
    st.markdown(html_content, unsafe_allow_html=True)

def main():
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
        
    current_lang = st.session_state.lang
    page_title = "Weather App" if current_lang == "en" else "Приложение за времето"
    st.set_page_config(page_title=page_title, page_icon="🌤️", layout="wide")
    
    # All App CSS (including new classes for our forecast cards)
    st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700; }
    
    /* Make Streamlit Tabs larger and wider */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 24px; height: auto; }
    .stTabs [data-baseweb="tab"] p { font-size: 1.4rem !important; font-weight: 700 !important; }

    /* COMPLETE PANEL HIDE: Hides the top deploy bar completely */
    [data-testid="stHeader"] { visibility: hidden; display: none; }
    
    /* --- CUSTOM FORECAST CARD CSS CLASSES --- */
    .forecast-card {
        text-align: center;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid var(--border-color, rgba(128,128,128,0.2));
        margin: 6px;
        box-shadow: 2px 4px 10px rgba(0,0,0,0.1);
    }
    .forecast-card.rain-bg {
        background-color: rgba(0, 180, 216, 0.1);
    }
    .forecast-time {
        font-weight: 700;
        font-size: 1.05em;
        margin-bottom: 5px;
        color: inherit;
    }
    .forecast-emoji {
        font-size: 3.2em;
        line-height: 1.2;
        margin-bottom: 0px;
    }
    .forecast-desc {
        font-size: 1em;
        font-weight: 700;
        color: #007BFF; /* Default Blue for standard weather */
        margin-bottom: 12px;
    }
    
    /* Dynamic Weather Text Colors */
    .forecast-desc.desc-thunderstorm {
        color: orange;
    }
    .forecast-desc.desc-hail {
        color: red;
    }
    
    .temp-primary {
        font-size: 1.1em;
        font-weight: 700;
    }
    .temp-secondary {
        font-size: 0.85em;
        opacity: 0.7;
    }
    .temp-tertiary {
        font-size: 0.9em;
        font-weight: 600;
        opacity: 0.9;
    }
    .mt-small { margin-top: 8px; }
    .mb-small { margin-bottom: 8px; }
    
    .forecast-divider {
        margin-top: 10px;
        border-top: 1px solid rgba(128,128,128,0.2);
        padding-top: 8px;
    }
    .forecast-extra {
        font-size: 0.85em;
        opacity: 0.7;
    }
    .forecast-rain {
        font-size: 0.95em;
        font-weight: 600;
        margin-top: 8px;
    }
    .forecast-rain.high-prob {
        color: #00B4D8;
    }

    /* --- APP HEADER (title + language selector) --- */
    .st-key-app_header {
        margin-bottom: 24px;
    }
    .st-key-app_header [data-testid="stMarkdownContainer"] h1 {
        font-weight: 700;
        letter-spacing: -0.01em;
        margin-top: 0;
    }
    .st-key-app_header [data-testid="stSelectbox"] {
        max-width: 220px;
    }

    /* --- LOCATION CARD (pre-fetch input section) ---
       NOTE: Streamlit does not actually define --secondary-background-color /
       --border-color as usable CSS custom properties in this version (verified:
       they resolve to empty at every scope), so the var() calls below always fall
       through to their literal fallback. Alpha values are tuned to be clearly
       visible against both a white and a near-black page background.
       The card is deliberately left without its own fill (border + shadow only):
       Streamlit's text inputs already render with its real theme-aware secondary
       background color, so giving the card a same-toned fill made the inputs
       visually disappear into it instead of standing out as the main fields. */
    .st-key-location_card {
        border-radius: 16px;
        border: 1px solid var(--border-color, rgba(128,128,128,0.35));
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        padding: 24px;
    }
    /* Streamlit's border=True paints its own border/shadow directly on the inner
       wrapper; !important overrides that inline styling so only the custom border
       above is visible instead of two stacked borders. */
    .st-key-location_card [data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
    }
    .st-key-location_card [data-testid="stTextInput"] label {
        font-weight: 600;
    }
    .st-key-location_card [data-testid="stTextInput"] input {
        border-radius: 8px;
        min-height: 44px;
    }

    /* --- LOCATE CHIP (geolocation button + hints, nested in the location card) --- */
    .st-key-locate_chip {
        border-radius: 12px;
        background: rgba(0, 180, 216, 0.06);
        padding: 16px;
        margin-bottom: 16px;
    }
    .st-key-locate_chip [data-testid="stVerticalBlock"] {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .st-key-locate_chip [data-testid="stCaptionContainer"]:first-of-type {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--text-color, inherit);
        opacity: 0.85;
    }
    .st-key-locate_chip [data-testid="stCaptionContainer"]:last-of-type {
        font-size: 0.78rem;
        font-weight: 400;
        opacity: 0.6;
    }
    /* The streamlit_geolocation component's iframe defaults to filling the full
       container width even though its actual button is a small square icon on a
       white background we can't restyle (it's the third-party bundle's own
       document). Rather than fight the white fill, cap the iframe to the icon's
       own footprint and frame it deliberately as a small bordered icon button. */
    .st-key-locate_chip [data-testid="stCustomComponentV1"] {
        width: 40px !important;
        max-width: 40px !important;
        border-radius: 8px;
        border: 1px solid rgba(128,128,128,0.3);
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        overflow: hidden;
    }

    /* --- MANUAL-ENTRY DIVIDER (replaces the plain "or enter manually" caption) ---
       Built as line/text/line flex items rather than a background-matching mask,
       so it never depends on knowing the exact page/card background color. */
    .location-divider {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-block: 16px;
    }
    .location-divider-line {
        flex: 1;
        height: 1px;
        background: var(--border-color, rgba(128,128,128,0.35));
    }
    .location-divider-text {
        font-size: 0.78rem;
        font-weight: 500;
        opacity: 0.6;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)

    # Set the translation based on the current session state
    t = TRANSLATIONS[current_lang]
    
    # --- Main Page Header Layout ---
    with st.container(key="app_header"):
        header_col1, header_col2 = st.columns([4, 1])

        with header_col1:
            st.title(t["app_title"])

        with header_col2:
            lang_opts = {"English": "en", "Български": "bg"}
            # The label t["lang_label"] is now clearly visible above the box!
            selected_lang_name = st.selectbox(
                label=t["lang_label"],
                options=list(lang_opts.keys()),
                index=0 if current_lang == "en" else 1,
                key="main_language_selector"
            )
            lang = lang_opts[selected_lang_name]
        
        # If the user changes the language, update session state and restart the app
        if lang != current_lang:
            st.session_state.lang = lang
            st.rerun()

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
        with st.container(key="locate_chip"):
            st.caption(t["geo_section_label"])
            geo_result = streamlit_geolocation()

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

            st.caption(t["geo_permission_hint"])

        st.markdown(
            '<div class="location-divider">'
            '<span class="location-divider-line"></span>'
            f'<span class="location-divider-text">{t["geo_divider_text"]}</span>'
            '<span class="location-divider-line"></span>'
            '</div>',
            unsafe_allow_html=True
        )

        c_in1, c_in2 = st.columns([1, 1])

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
    if using_geo_location and not st.session_state.geo_location.get("country"):
        st.session_state.geo_location["name"] = t["geo_header_generic"]

    if using_geo_location or city_input:
        with st.spinner(t["fetching"]):
            location = (
                st.session_state.geo_location if using_geo_location
                else get_coordinates(city_input, country_input)
            )

            if location:
                lat, lon = location["latitude"], location["longitude"]
                f_data = get_weather_data(lat, lon)
                
                if f_data:
                    hourly = f_data.get("hourly", {})
                    daily = f_data.get("daily", {})
                    curr = f_data.get("current", {})
                    
                    # Compute Daily Average Humidity
                    daily_hum_list = calculate_daily_average_humidity(hourly.get("relative_humidity_2m", []))

                    # --- Main Screen Metrics ---
                    location_label = location["name"]
                    if location.get("country"):
                        location_label += f", {location['country']}"
                    st.header(f"📍 {location_label}")

                    if using_geo_location and not location.get("country"):
                        st.info(t["geo_reverse_lookup_failed"])

                    m1, m2, m3, m4, m5, m6 = st.columns(6)
                    with m1:
                        st.metric(t["current_temp"], f"{curr.get('temperature_2m', '--')}°C")
                    with m2:
                        st.metric(t["real_feel"], f"{curr.get('apparent_temperature', '--')}°C")
                    with m3:
                        st.metric(t["max_temp"], f"{safe_get(daily, 'temperature_2m_max', 0, '--')}°C")
                    with m4:
                        st.metric(t["min_temp"], f"{safe_get(daily, 'temperature_2m_min', 0, '--')}°C")
                    with m5:
                        wind_speed_val = curr.get('wind_speed_10m', '--')
                        wind_unit = "km/h" if lang == "en" else "км/ч"
                        st.metric(t["wind_speed"], f"{wind_speed_val} {wind_unit}")
                    with m6:
                        st.metric(t["humidity"], f"{curr.get('relative_humidity_2m', '--')}%")

                    st.divider()

                    # --- Alerts Section ---
                    if daily and "time" in daily:
                        st.subheader(t["alerts_header"].format(city=location['name']))
                        alerts = get_weather_alerts(daily, lang=lang)
                        
                        if alerts:
                            for alert in alerts:
                                if alert["type"] == "error":
                                    st.error(alert["message"])
                                else:
                                    st.warning(alert["message"])
                        else:
                            st.success(t["no_alerts"].format(city=location['name']))
                    
                    st.divider()

                    # --- Immediate 24h Hourly Track ---
                    if hourly and "time" in hourly:
                        st.subheader(t["next_24h"])
                        num_hours = min(24, len(hourly["time"]))
                        for i in range(0, num_hours, 6):
                            cols = st.columns(6)
                            for j in range(6):
                                idx = i + j
                                if idx < num_hours:
                                    day_str = hourly["time"][idx][:10]
                                    try:
                                        d_idx = daily["time"].index(day_str)
                                        d_min = safe_get(daily, "temperature_2m_min", d_idx)
                                        d_max = safe_get(daily, "temperature_2m_max", d_idx)
                                    except ValueError:
                                        d_min, d_max = None, None
                                        
                                    with cols[j]:
                                        render_forecast_card(
                                            hourly["time"][idx],
                                            code=safe_get(hourly, "weather_code", idx),
                                            rain_prob=safe_get(hourly, "precipitation_probability", idx),
                                            wind=safe_get(hourly, "wind_speed_10m", idx),
                                            humidity=safe_get(hourly, "relative_humidity_2m", idx),
                                            max_t=d_max,
                                            min_t=d_min,
                                            hour_t=safe_get(hourly, "temperature_2m", idx),
                                            hour_app=safe_get(hourly, "apparent_temperature", idx),
                                            is_hourly=True,
                                            lang=lang
                                        )
                    else:
                        st.warning(t["hourly_unavailable"])

                    st.divider()

                    # --- Helper function to display card + button ---
                    def display_daily_column(st_col, data_index, tab_prefix):
                        hum_val = daily_hum_list[data_index] if data_index < len(daily_hum_list) else None
                        with st_col:
                            render_forecast_card(
                                daily["time"][data_index],
                                code=safe_get(daily, "weather_code", data_index),
                                rain_prob=safe_get(daily, "precipitation_probability_max", data_index),
                                wind=safe_get(daily, "wind_speed_10m_max", data_index),
                                humidity=hum_val,
                                max_t=safe_get(daily, "temperature_2m_max", data_index),
                                min_t=safe_get(daily, "temperature_2m_min", data_index),
                                app_max=safe_get(daily, "apparent_temperature_max", data_index),
                                app_min=safe_get(daily, "apparent_temperature_min", data_index),
                                is_hourly=False,
                                lang=lang
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
                            num_7 = min(7, len(daily["time"]))
                            cols = st.columns(7)
                            for i in range(num_7):
                                display_daily_column(cols[i], i, "tab7")
                        
                        with tab14:
                            num_14 = min(14, len(daily["time"]))
                            for row in range((num_14 + 6) // 7):
                                cols = st.columns(7)
                                for col in range(7):
                                    idx = row * 7 + col
                                    if idx < num_14:
                                        display_daily_column(cols[col], idx, "tab14")
                                            
                        with tab_radar:
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # --- BIG REDIRECT BUTTON TO WINDY.COM ---
                            windy_redirect_url = f"https://www.windy.com/-Weather-radar-radar?radar,{lat},{lon},6"
                            st.link_button(t["open_windy"], url=windy_redirect_url, type="primary")
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Keeps the embedded preview view visible just underneath
                            st.markdown(
                                f"<iframe width='100%' height='600' src='https://embed.windy.com/embed2.html?lat={lat}&lon={lon}&zoom=6&level=surface&overlay=radar&product=radar&menu=&message=true&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1&play=1' frameborder='0' style='border-radius: 12px; box-shadow: 2px 4px 12px rgba(0,0,0,0.1);'></iframe>", 
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
                                for i in range(0, len(day_indices), 6):
                                    cols = st.columns(6)
                                    for j in range(6):
                                        if i + j < len(day_indices):
                                            idx = day_indices[i + j]
                                            
                                            try:
                                                d_idx = daily["time"].index(sel_date)
                                                d_min = safe_get(daily, "temperature_2m_min", d_idx)
                                                d_max = safe_get(daily, "temperature_2m_max", d_idx)
                                            except ValueError:
                                                d_min, d_max = None, None
                                                
                                            with cols[j]:
                                                render_forecast_card(
                                                    hourly["time"][idx],
                                                    code=safe_get(hourly, "weather_code", idx),
                                                    rain_prob=safe_get(hourly, "precipitation_probability", idx),
                                                    wind=safe_get(hourly, "wind_speed_10m", idx),
                                                    humidity=safe_get(hourly, "relative_humidity_2m", idx),
                                                    max_t=d_max,
                                                    min_t=d_min,
                                                    hour_t=safe_get(hourly, "temperature_2m", idx),
                                                    hour_app=safe_get(hourly, "apparent_temperature", idx),
                                                    is_hourly=True,
                                                    lang=lang
                                                )
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