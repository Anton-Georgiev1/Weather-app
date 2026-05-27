import streamlit as st
import httpx
import pandas as pd

# --- Configuration ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

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
    65: ("Heavy Rain", "🌧️"),
    66: ("Freezing Rain: Light", "🌨️"),
    67: ("Heavy Freezing Rain", "🌨️"),
    71: ("Snow fall: Slight", "❄️"),
    73: ("Snow fall: Moderate", "❄️"),
    75: ("Heavy Snow Fall", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Rain showers: Slight", "🌦️"),
    81: ("Rain showers: Moderate", "🌦️"),
    82: ("Violent Rain Showers", "🌦️"),
    85: ("Snow showers: Slight", "🌨️"),
    86: ("Heavy Snow Showers", "🌨️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"),
    99: ("Severe Thunderstorm", "⛈️"),
}

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

def render_forecast_card(date_str, code, rain_prob, wind=None, humidity=None, 
                         max_t=None, min_t=None, app_max=None, app_min=None, 
                         hour_t=None, hour_app=None, is_hourly=False):
    try:
        date_obj = pd.to_datetime(date_str)
        label = date_obj.strftime("%H:00") if is_hourly else date_obj.strftime("%A, %d %b")
    except Exception:
        label = "Unknown"
    
    code = code if code is not None else -1
    desc, emoji = WMO_CODES.get(code, ("Unknown", "❓"))
    
    try:
        rain_prob_val = int(rain_prob)
    except (ValueError, TypeError):
        rain_prob_val = 0
        
    rain_color = "#00B4D8" if rain_prob_val > 20 else "inherit"
    bg_style = "background-color: rgba(0, 180, 216, 0.1);" if rain_prob_val > 30 else ""
    
    wind_str = f"{round(wind, 1)} km/h" if wind is not None else "-- km/h"
    humidity_str = f"{int(humidity)}%" if humidity is not None else "--%"
    max_t_str = f"{round(max_t, 1)}°" if max_t is not None else "--°"
    min_t_str = f"{round(min_t, 1)}°" if min_t is not None else "--°"
    
    if is_hourly:
        hour_t_str = f"{round(hour_t, 1)}°" if hour_t is not None else "--°"
        hour_app_str = f"{round(hour_app, 1)}°" if hour_app is not None else "--°"
        temp_html = (
            f"<div style='font-size: 1.15em; font-weight: 700;'>Current Temp: {hour_t_str}</div>"
            f"<div style='font-size: 0.9em; opacity: 0.7; margin-bottom: 8px;'>Feels like {hour_app_str}</div>"
            f"<div style='font-size: 0.9em; font-weight: 600; opacity: 0.9;'>Day Max: {max_t_str}</div>"
            f"<div style='font-size: 0.9em; font-weight: 600; opacity: 0.9; margin-bottom: 8px;'>Day Min: {min_t_str}</div>"
        )
    else:
        app_max_str = f"{round(app_max, 1)}°" if app_max is not None else "--°"
        app_min_str = f"{round(app_min, 1)}°" if app_min is not None else "--°"
        temp_html = (
            f"<div style='font-size: 1.1em; font-weight: 700;'>Max: {max_t_str}</div>"
            f"<div style='font-size: 0.85em; opacity: 0.7;'>Feels like {app_max_str}</div>"
            f"<div style='font-size: 1.1em; font-weight: 600; margin-top: 8px;'>Min: {min_t_str}</div>"
            f"<div style='font-size: 0.85em; opacity: 0.7; margin-bottom: 8px;'>Feels like {app_min_str}</div>"
        )

    rain_html = f"<div style='font-size: 0.95em; color: {rain_color}; font-weight: 600; margin-top: 8px;'>Rain chance: {rain_prob_val}%</div>"
    
    extra_info = (
        f"<div style='font-size: 0.85em; opacity: 0.7;'>Hum: {humidity_str}</div>"
        f"<div style='font-size: 0.85em; opacity: 0.7;'>Wind: {wind_str}</div>"
    )

    html_content = (
        f"<div style='text-align: center; padding: 20px; border-radius: 16px; border: 1px solid var(--border-color, rgba(128,128,128,0.2)); {bg_style} margin: 6px; box-shadow: 2px 4px 10px rgba(0,0,0,0.1);'>"
        f"<div style='font-weight: 700; font-size: 1.05em; margin-bottom: 5px; color: inherit;'>{label}</div>"
        f"<div style='font-size: 3.2em; margin-bottom: 0px;'>{emoji}</div>"
        f"<div style='font-size: 1em; font-weight: 700; color: #007BFF; margin-bottom: 12px;'>{desc}</div>"
        f"{temp_html}"
        f"<div style='margin-top: 10px; border-top: 1px solid rgba(128,128,128,0.2); padding-top: 8px;'>"
        f"{extra_info}"
        f"{rain_html}"
        f"</div>"
        f"</div>"
    )
    st.markdown(html_content, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Weather Pro", page_icon="🌤️", layout="wide")
    
    # Custom CSS for bigger metrics AND significantly wider/larger Tab Headers
    st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700; }
    
    /* Make Streamlit Tabs larger and wider */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 24px;
        height: auto;
    }
    .stTabs [data-baseweb="tab"] p {
        font-size: 1.4rem !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Weather Pro Dashboard 🌤️")

    # Initialize session states for specific day drill-down
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None
    if "last_city" not in st.session_state:
        st.session_state.last_city = ""

    # Input Layout 
    c_in1, c_in2 = st.columns([1, 1])
    with c_in1:
        city_input = st.text_input("City", placeholder="Enter city name...")
    with c_in2:
        country_input = st.text_input("Country (Optional)", placeholder="Enter country name...")

    # Clear selected day when user searches for a new city
    if city_input and city_input != st.session_state.last_city:
        st.session_state.selected_date = None
        st.session_state.last_city = city_input

    if city_input:
        with st.spinner("Fetching weather data..."):
            location = get_coordinates(city_input, country_input)
            
            if location:
                lat, lon = location["latitude"], location["longitude"]
                f_data = get_weather_data(lat, lon)
                
                if f_data:
                    hourly = f_data.get("hourly", {})
                    daily = f_data.get("daily", {})
                    curr = f_data.get("current", {})
                    
                    # Compute Daily Average Humidity
                    daily_hum_list = []
                    hourly_hum_data = hourly.get("relative_humidity_2m", [])
                    if hourly_hum_data:
                        for i in range(0, len(hourly_hum_data), 24):
                            chunk = [x for x in hourly_hum_data[i:i+24] if x is not None]
                            daily_hum_list.append(sum(chunk) / len(chunk) if chunk else None)

                    # --- Main Screen Metrics ---
                    st.header(f"📍 {location['name']}, {location.get('country', '')}")
                    
                    m1, m2, m3, m4, m5, m6 = st.columns(6)
                    with m1:
                        st.metric("Current Temp", f"{curr.get('temperature_2m', '--')}°C")
                    with m2:
                        st.metric("Real Feel", f"{curr.get('apparent_temperature', '--')}°C")
                    with m3:
                        st.metric("Max Temp", f"{safe_get(daily, 'temperature_2m_max', 0, '--')}°C")
                    with m4:
                        st.metric("Min Temp", f"{safe_get(daily, 'temperature_2m_min', 0, '--')}°C")
                    with m5:
                        st.metric("Wind Speed", f"{curr.get('wind_speed_10m', '--')} km/h")
                    with m6:
                        st.metric("Humidity", f"{curr.get('relative_humidity_2m', '--')}%")

                    st.divider()

                    # --- Alerts Section ---
                    if daily and "time" in daily:
                        has_alerts = False
                        st.subheader(f"⚠️ Weather Alerts for {location['name']}")
                        
                        for i in range(len(daily["time"])):
                            wcode = safe_get(daily, "weather_code", i)
                            prob = safe_get(daily, "precipitation_probability_max", i, 0)
                            wind = safe_get(daily, "wind_speed_10m_max", i, 0)
                            day_name = pd.to_datetime(daily["time"][i]).strftime("%A, %B %d")
                            
                            if wcode in [65, 67, 75, 82, 86, 95, 96, 99]:
                                condition_name = WMO_CODES.get(wcode, ("Severe Weather", ""))[0]
                                st.error(f"**Alert for {day_name}:** {condition_name} expected! (**{prob}%** chance of precipitation)")
                                has_alerts = True
                            
                            if wind is not None and wind > 50:
                                st.warning(f"**Wind Advisory for {day_name}:** High wind speeds expected up to **{wind} km/h**.")
                                has_alerts = True
                                
                        if not has_alerts:
                            st.success(f"No severe storms or high wind alerts detected for {location['name']} over the next 14 days.")
                    
                    st.divider()

                    # --- Immediate 24h Hourly Track ---
                    if hourly and "time" in hourly:
                        st.subheader("Immediate Next 24 Hours")
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
                                            is_hourly=True
                                        )
                    else:
                        st.warning("Hourly data unavailable.")

                    st.divider()

                    # --- Helper function to display card + button ---
                    # We pass 'tab_prefix' so buttons in the 7-day tab and 14-day tab get completely unique keys!
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
                                is_hourly=False
                            )
                            # UNIQUE KEY: combining the tab name and the date
                            btn_key = f"btn_{tab_prefix}_{daily['time'][data_index]}"
                            if st.button("🕐 24h View", key=btn_key, use_container_width=True):
                                st.session_state.selected_date = daily["time"][data_index]
                                st.rerun()

                    # --- Long Term Forecasts & Radar Tabs ---
                    if daily and "time" in daily:
                        tab7, tab14, tab_radar = st.tabs(["7-Day Forecast", "14-Day Forecast", "Live Radar 📡"])
                        
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
                            st.markdown(f"""
                                <iframe width="100%" height="600" src="https://embed.windy.com/embed2.html?lat={lat}&lon={lon}&zoom=6&level=surface&overlay=radar&product=radar&menu=&message=true&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1" frameborder="0" style="border-radius: 12px; box-shadow: 2px 4px 12px rgba(0,0,0,0.1);"></iframe>
                            """, unsafe_allow_html=True)
                            st.caption(f"Interactive Live Radar is actively centered on {location['name']}.")

                        # --- Specific Day Clicked Section ---
                        if st.session_state.selected_date:
                            st.divider()
                            sel_date = st.session_state.selected_date
                            formatted_sel_date = pd.to_datetime(sel_date).strftime("%A, %B %d")
                            
                            st.subheader(f"🕒 Specific Hourly Forecast for {formatted_sel_date}")
                            
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
                                                    is_hourly=True
                                                )
                            else:
                                st.info("Hourly breakdown data is not available this far in the future.")

                    else:
                        st.warning("Daily forecast data unavailable.")
                else:
                    st.error("Failed to retrieve weather data. Try a different city.")
            else:
                st.warning("Location not found. Please verify the city and country name.")

if __name__ == "__main__":
    main()