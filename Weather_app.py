import streamlit as st
import httpx
import pandas as pd

# --- Configuration ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
SEASONAL_API_URL = "https://seasonal-api.open-meteo.com/v1/seasonal"

WMO_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Drizzle: Light", "🌦️"),
    53: ("Drizzle: Moderate", "🌦️"),
    55: ("Drizzle: Dense", "🌦️"),
    56: ("Freezing Drizzle: Light", "🌨️"),
    57: ("Freezing Drizzle: Dense", "🌨️"),
    61: ("Rain: Slight", "🌧️"),
    63: ("Rain: Moderate", "🌧️"),
    65: ("Rain: Heavy", "🌧️"),
    66: ("Freezing Rain: Light", "🌨️"),
    67: ("Freezing Rain: Heavy", "🌨️"),
    71: ("Snow fall: Slight", "❄️"),
    73: ("Snow fall: Moderate", "❄️"),
    75: ("Snow fall: Heavy", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Rain showers: Slight", "🌦️"),
    81: ("Rain showers: Moderate", "🌦️"),
    82: ("Rain showers: Violent", "🌦️"),
    85: ("Snow showers: Slight", "🌨️"),
    86: ("Snow showers: Heavy", "🌨️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}

def safe_get(data_dict, key, idx, default=None):
    """Safely fetch index from dictionary arrays to prevent IndexErrors on missing API data."""
    if not isinstance(data_dict, dict):
        return default
    arr = data_dict.get(key, [])
    if isinstance(arr, list) and idx < len(arr) and arr[idx] is not None:
        return arr[idx]
    return default

def get_ip_location():
    """Fetches user's current city based on IP address."""
    try:
        resp = httpx.get("https://ipapi.co/json/", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("city", ""), data.get("country_name", "")
    except Exception:
        pass
    return "", ""

def auto_locate():
    """Callback for the Auto-Locate button."""
    city, country = get_ip_location()
    if city:
        st.session_state.city_input = city
        st.session_state.country_input = country

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

def get_weather_data(lat: float, lon: float):
    f_params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "temperature_2m,relative_humidity_2m,weathercode,precipitation_probability,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": 16
    }
    s_params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min",
    }
    
    f_data, s_data = None, None
    try:
        f_resp = httpx.get(WEATHER_API_URL, params=f_params, timeout=10)
        f_resp.raise_for_status()
        f_data = f_resp.json()
    except Exception:
        pass
        
    try:
        s_resp = httpx.get(SEASONAL_API_URL, params=s_params, timeout=10)
        if s_resp.status_code == 200:
            s_data = s_resp.json()
    except Exception: 
        pass
        
    return f_data, s_data

def render_forecast_card(date_str, max_t, min_t, code, rain_prob, wind=None, humidity=None, is_hourly=False):
    try:
        date_obj = pd.to_datetime(date_str)
        if is_hourly:
            label = date_obj.strftime("%H:00")
        else:
            label = date_obj.strftime("%a %d")
    except Exception:
        label = "Unknown"
    
    code = code if code is not None else -1
    _, emoji = WMO_CODES.get(code, ("Unknown", "❓"))
    
    try:
        rain_prob_val = int(rain_prob)
    except (ValueError, TypeError):
        rain_prob_val = 0
        
    rain_color = "#00B4D8" if rain_prob_val > 20 else "inherit"
    bg_style = "background-color: rgba(0, 180, 216, 0.1);" if rain_prob_val > 30 else ""
    
    # Formatting values
    wind_str = f"{round(wind, 1)} km/h" if wind is not None else "-- km/h"
    humidity_str = f"{int(humidity)}%" if humidity is not None else "--%"
    max_t_str = f"{round(max_t, 1)}°" if max_t is not None else "--°"
    min_t_str = f"{round(min_t, 1)}°" if min_t is not None else "--°"
    
    # Build text blocks without indents to prevent Streamlit from wrapping in code blocks
    if is_hourly:
        temp_html = f"<div style='font-size: 1.1em; font-weight: 700; margin-bottom: 8px;'>Temp: {max_t_str}</div>"
    else:
        temp_html = (
            f"<div style='font-size: 1.1em; font-weight: 700;'>Max: {max_t_str}</div>"
            f"<div style='font-size: 0.9em; opacity: 0.7; margin-bottom: 8px;'>Min: {min_t_str}</div>"
        )

    rain_html = f"<div style='font-size: 0.9em; color: {rain_color}; font-weight: 600; margin-top: 5px;'>Rain chance: {rain_prob_val}%</div>"
    
    extra_info = (
        f"<div style='font-size: 0.85em; opacity: 0.7;'>Hum: {humidity_str}</div>"
        f"<div style='font-size: 0.85em; opacity: 0.7;'>Wind: {wind_str}</div>"
    )

    # Increased padding (16px), font sizes, and min-width (140px)
    html_content = (
        f"<div style='text-align: center; padding: 16px; border-radius: 12px; border: 1px solid var(--border-color, rgba(128,128,128,0.2)); {bg_style} min-width: 140px; margin: 5px; box-shadow: 2px 2px 8px rgba(0,0,0,0.1);'>"
        f"<div style='font-weight: 600; font-size: 1em; margin-bottom: 5px; color: inherit;'>{label}</div>"
        f"<div style='font-size: 2.5em; margin-bottom: 8px;'>{emoji}</div>"
        f"{temp_html}"
        f"{extra_info}"
        f"{rain_html}"
        f"</div>"
    )
    
    st.markdown(html_content, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Weather Pro", page_icon="🌤️", layout="wide")
    
    # Custom CSS: Make metrics large and hide Streamlit's settings menu (so users can't reset theme to System)
    st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; font-weight: 700; }
    #MainMenu {visibility: hidden;} /* Hides standard Streamlit menu */
    header {visibility: hidden;}    /* Hides top right header menu */
    </style>
    """, unsafe_allow_html=True)

    st.title("Weather Pro Dashboard 🌤️")
    
    # Setup session state for auto-locate
    if "city_input" not in st.session_state:
        st.session_state.city_input = ""
    if "country_input" not in st.session_state:
        st.session_state.country_input = ""
    
    # Input Layout 
    c_in1, c_in2, c_btn = st.columns([3, 3, 2])
    with c_in1:
        st.text_input("City", key="city_input", placeholder="Enter city name...")
    with c_in2:
        st.text_input("Country (Optional)", key="country_input", placeholder="Enter country name...")
    with c_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        st.button("📍 Auto-Locate Me", on_click=auto_locate, help="Detects your current city using your IP address.")

    city = st.session_state.city_input
    country = st.session_state.country_input

    if city:
        with st.spinner("Fetching weather data..."):
            location = get_coordinates(city, country)
            
            if location:
                lat, lon = location["latitude"], location["longitude"]
                f_data, s_data = get_weather_data(lat, lon)
                
                if f_data:
                    # --- Compute Daily Average Humidity from Hourly Data ---
                    hourly = f_data.get("hourly", {})
                    daily = f_data.get("daily", {})
                    
                    daily_hum_list = []
                    hourly_hum_data = hourly.get("relative_humidity_2m", [])
                    if hourly_hum_data:
                        # Group 384 hours into 24-hour chunks (16 days total)
                        for i in range(0, len(hourly_hum_data), 24):
                            chunk = [x for x in hourly_hum_data[i:i+24] if x is not None]
                            if chunk:
                                daily_hum_list.append(sum(chunk) / len(chunk))
                            else:
                                daily_hum_list.append(None)
                                
                    # --- Current & Radar Section ---
                    st.header(f"{location['name']}, {location.get('country', '')}")
                    hero_col, radar_col = st.columns([1, 2])
                    
                    with hero_col:
                        curr = f_data.get("current_weather", {})
                        wmo_code = curr.get("weathercode", -1)
                        wmo, emoji = WMO_CODES.get(wmo_code, ("Unknown", "❓"))
                        
                        st.metric("Current Temperature", f"{curr.get('temperature', 'N/A')}°C")
                        st.markdown(f"## {emoji} {wmo}")
                        st.metric("Wind Speed", f"{curr.get('windspeed', 'N/A')} km/h")
                        
                        humidity_val = safe_get(hourly, "relative_humidity_2m", 0)
                        if humidity_val is not None:
                            st.metric("Humidity", f"{humidity_val}%")
                    
                    with radar_col:
                        st.subheader("Interactive Radar (Windy)")
                        # Radar natively auto-locates via coordinates (lat/lon passed in URL)
                        st.markdown(f"""
                            <iframe width="100%" height="500" src="https://embed.windy.com/embed2.html?lat={lat}&lon={lon}&zoom=6&level=surface&overlay=radar&product=radar&menu=&message=true&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1" frameborder="0"></iframe>
                        """, unsafe_allow_html=True)
                        st.caption(f"Radar successfully auto-centered on {location['name']}.")

                    st.divider()

                    # --- 24h Hourly Track ---
                    if hourly and "time" in hourly:
                        st.subheader("Next 24 Hours")
                        num_hours = min(24, len(hourly["time"]))
                        for i in range(0, num_hours, 6):  # Changed to 6 per row due to larger sizes
                            cols = st.columns(6)
                            for j in range(6):
                                idx = i + j
                                if idx < num_hours:
                                    with cols[j]:
                                        render_forecast_card(
                                            hourly["time"][idx],
                                            max_t=safe_get(hourly, "temperature_2m", idx),
                                            min_t=None,
                                            code=safe_get(hourly, "weathercode", idx),
                                            rain_prob=safe_get(hourly, "precipitation_probability", idx),
                                            wind=safe_get(hourly, "wind_speed_10m", idx),
                                            humidity=safe_get(hourly, "relative_humidity_2m", idx),
                                            is_hourly=True
                                        )
                    else:
                        st.warning("Hourly data unavailable.")

                    st.divider()

                    # --- Long Term Forecasts ---
                    if daily and "time" in daily:
                        tab7, tab14, tab30 = st.tabs(["7-Day Forecast", "14-Day Forecast", "30-Day Trend"])
                        
                        with tab7:
                            num_7 = min(7, len(daily["time"]))
                            cols = st.columns(7)
                            for i in range(num_7):
                                hum_val = daily_hum_list[i] if i < len(daily_hum_list) else None
                                with cols[i]:
                                    render_forecast_card(
                                        daily["time"][i],
                                        max_t=safe_get(daily, "temperature_2m_max", i),
                                        min_t=safe_get(daily, "temperature_2m_min", i),
                                        code=safe_get(daily, "weathercode", i),
                                        rain_prob=safe_get(daily, "precipitation_probability_max", i),
                                        wind=safe_get(daily, "wind_speed_10m_max", i),
                                        humidity=hum_val
                                    )
                        
                        with tab14:
                            num_14 = min(14, len(daily["time"]))
                            for row in range((num_14 + 6) // 7):
                                cols = st.columns(7)
                                for col in range(7):
                                    idx = row * 7 + col
                                    if idx < num_14:
                                        hum_val = daily_hum_list[idx] if idx < len(daily_hum_list) else None
                                        with cols[col]:
                                            render_forecast_card(
                                                daily["time"][idx],
                                                max_t=safe_get(daily, "temperature_2m_max", idx),
                                                min_t=safe_get(daily, "temperature_2m_min", idx),
                                                code=safe_get(daily, "weathercode", idx),
                                                rain_prob=safe_get(daily, "precipitation_probability_max", idx),
                                                wind=safe_get(daily, "wind_speed_10m_max", idx),
                                                humidity=hum_val
                                            )

                        with tab30:
                            s_daily = s_data.get("daily", {}) if s_data else {}
                            if s_daily and "time" in s_daily:
                                num_30 = min(30, len(s_daily["time"]))
                                for i in range(0, num_30, 7):
                                    cols = st.columns(7)
                                    for j in range(7):
                                        idx = i + j
                                        if idx < num_30:
                                            with cols[j]:
                                                # Seasonal API doesn't provide 30-day wind/humidity, safely rendered as "--"
                                                render_forecast_card(
                                                    s_daily["time"][idx],
                                                    max_t=safe_get(s_daily, "temperature_2m_max", idx),
                                                    min_t=safe_get(s_daily, "temperature_2m_min", idx),
                                                    code=0, 
                                                    rain_prob=0
                                                )
                            else:
                                st.info("30-day seasonal data not available. Showing 16-day trend.")
                                num_16 = len(daily["time"])
                                for i in range(0, num_16, 7):
                                    cols = st.columns(7) 
                                    for j in range(7):
                                        idx = i + j
                                        if idx < num_16:
                                            hum_val = daily_hum_list[idx] if idx < len(daily_hum_list) else None
                                            with cols[j]:
                                                render_forecast_card(
                                                    daily["time"][idx],
                                                    max_t=safe_get(daily, "temperature_2m_max", idx),
                                                    min_t=safe_get(daily, "temperature_2m_min", idx),
                                                    code=safe_get(daily, "weathercode", idx),
                                                    rain_prob=safe_get(daily, "precipitation_probability_max", idx),
                                                    wind=safe_get(daily, "wind_speed_10m_max", idx),
                                                    humidity=hum_val
                                                )
                    else:
                        st.warning("Daily forecast data unavailable.")

                else:
                    st.error("Failed to retrieve weather data. Try a different city.")
            else:
                st.warning("Location not found. Please verify the city and country name.")

if __name__ == "__main__":
    main()