import streamlit as st
import httpx
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components

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

def get_coordinates(city: str, country: str | None = None) -> dict | None:
    """Fetch latitude and longitude for a city and country."""
    query = city.strip()
    if not query: return None
    if country and country.strip(): query += f", {country.strip()}"
    params = {"name": query, "count": 1, "language": "en", "format": "json"}
    try:
        response = httpx.get(GEOCODING_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["results"][0] if "results" in data and data["results"] else None
    except Exception: return None

def get_weather_data(lat: float, lon: float):
    """Fetch 16-day and seasonal 30-day weather data."""
    # Standard 16-day forecast
    f_params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max,precipitation_sum",
        "timezone": "auto",
        "forecast_days": 16
    }
    # Seasonal 30-day (using seasonal-api for trend)
    s_params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min",
    }
    
    try:
        f_resp = httpx.get(WEATHER_API_URL, params=f_params, timeout=10)
        f_resp.raise_for_status()
        f_data = f_resp.json()
        
        # Try to get seasonal data for the "month" view
        s_resp = httpx.get(SEASONAL_API_URL, params=s_params, timeout=10)
        s_data = s_resp.json() if s_resp.status_code == 200 else None
        
        return f_data, s_data
    except Exception: return None, None

def render_weather_card(date_str, max_t, min_t, code, rain_prob, rain_sum=None):
    date_obj = pd.to_datetime(date_str)
    day_name = date_obj.strftime("%a")
    day_num = date_obj.strftime("%d")
    _, emoji = WMO_CODES.get(code, ("Unknown", "❓"))
    
    # Rain Intuition: Highlight if rain chance > 30%
    border_style = "border: 2px solid #00B4D8;" if rain_prob > 30 else "border: 1px solid #ddd;"
    bg_color = "background-color: #E0F2F1;" if rain_prob > 30 else "background-color: transparent;"
    
    st.markdown(f"""
    <div style="text-align: center; padding: 10px; border-radius: 10px; {border_style} {bg_color} min-width: 80px;">
        <div style="font-weight: bold; font-size: 0.9em;">{day_name} {day_num}</div>
        <div style="font-size: 2em; margin: 5px 0;">{emoji}</div>
        <div style="font-weight: bold;">{max_t}°</div>
        <div style="color: #666; font-size: 0.9em;">{min_t}°</div>
        <div style="color: #0077B6; font-size: 0.8em; margin-top: 5px;">💧{rain_prob}%</div>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Advanced Weather", page_icon="🌤️", layout="wide")
    
    # Custom CSS for AccuWeather-like look
    st.markdown("""
    <style>
    .main { background-color: inherit; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

    st.title("Weather Dashboard 🌤️")
    
    col_input1, col_input2 = st.columns([1, 1])
    with col_input1:
        city = st.text_input("City", placeholder="e.g. Sofia")
    with col_input2:
        country = st.text_input("Country (Optional)", placeholder="e.g. Bulgaria")

    if city:
        location = get_coordinates(city, country)
        if location:
            lat, lon = location["latitude"], location["longitude"]
            f_data, s_data = get_weather_data(lat, lon)
            
            if f_data:
                # --- HERO SECTION ---
                curr = f_data["current_weather"]
                wmo, emoji = WMO_CODES.get(curr["weathercode"], ("Unknown", "❓"))
                
                st.header(f"{location['name']}, {location.get('country', '')}")
                
                c1, c2, r_col = st.columns([1, 1, 2])
                with c1:
                    st.metric("Current", f"{curr['temperature']}°C", help="Temperature right now")
                    st.markdown(f"### {emoji} {wmo}")
                with c2:
                    st.metric("Wind", f"{curr['windspeed']} km/h")
                    # Real feel estimation or extra data can go here
                
                with r_col:
                    st.subheader("Interactive Radar")
                    # Radar synced to location
                    radar_url = f"https://www.rainviewer.com/map.html?lat={lat}&lon={lon}&zoom=6&type=1&size=512&color=1&tm=1&v=1"
                    components.iframe(radar_url, height=300)

                # --- FORECASTS ---
                st.divider()
                
                # Tabbed Forecasts
                tab7, tab14, tab30 = st.tabs(["7-Day Forecast", "14-Day Forecast", "30-Day Outlook"])
                
                daily = f_data["daily"]
                
                with tab7:
                    st.subheader("Coming Week")
                    cols = st.columns(7)
                    for i in range(7):
                        with cols[i]:
                            render_weather_card(
                                daily["time"][i], 
                                daily["temperature_2m_max"][i], 
                                daily["temperature_2m_min"][i], 
                                daily["weathercode"][i], 
                                daily["precipitation_probability_max"][i]
                            )
                    
                    # Rain probability chart for intuition
                    st.markdown("#### Rain Probability Next 7 Days")
                    df_7 = pd.DataFrame({
                        "Date": pd.to_datetime(daily["time"][:7]),
                        "Rain Chance (%)": daily["precipitation_probability_max"][:7]
                    }).set_index("Date")
                    st.bar_chart(df_7, color="#00B4D8")

                with tab14:
                    st.subheader("Next 2 Weeks")
                    # Grid layout for 14 days
                    for row in range(2):
                        cols = st.columns(7)
                        for col in range(7):
                            idx = row * 7 + col
                            if idx < 14:
                                with cols[col]:
                                    render_weather_card(
                                        daily["time"][idx], 
                                        daily["temperature_2m_max"][idx], 
                                        daily["temperature_2m_min"][idx], 
                                        daily["weathercode"][idx], 
                                        daily["precipitation_probability_max"][idx]
                                    )
                    
                with tab30:
                    st.subheader("30-Day Seasonal Trend")
                    if s_data and "daily" in s_data:
                        s_daily = s_data["daily"]
                        df_30 = pd.DataFrame({
                            "Date": pd.to_datetime(s_daily["time"][:30]),
                            "Max Temp Trend (°C)": s_daily["temperature_2m_max"][:30],
                            "Min Temp Trend (°C)": s_daily["temperature_2m_min"][:30]
                        }).set_index("Date")
                        
                        st.line_chart(df_30)
                        st.caption("Note: 30-day data is based on seasonal ensemble models (trends).")
                        
                        # Show as table for detailed check
                        with st.expander("See full 30-day table"):
                            st.dataframe(df_30, use_container_width=True)
                    else:
                        # Fallback: Repeat 14-day data or show info
                        st.info("High-resolution 30-day forecast is unavailable. Showing trend for next 16 days.")
                        df_16 = pd.DataFrame({
                            "Date": pd.to_datetime(daily["time"]),
                            "Max Temp": daily["temperature_2m_max"],
                            "Min Temp": daily["temperature_2m_min"]
                        }).set_index("Date")
                        st.line_chart(df_16)

        else:
            st.warning("Location not found. Try adding the country name.")

if __name__ == "__main__":
    main()
