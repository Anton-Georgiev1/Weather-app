import streamlit as st
import httpx
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

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
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}

def get_coordinates(city: str, country: str | None = None) -> dict | None:
    """Fetch latitude and longitude for a city and country."""
    query = city.strip()
    if not query:
        return None
    if country and country.strip():
        query += f", {country.strip()}"
    params = {"name": query, "count": 1, "language": "en", "format": "json"}
    response = httpx.get(GEOCODING_API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data["results"][0] if "results" in data and data["results"] else None

def get_weather(lat: float, lon: float) -> dict | None:
    """Fetch 14-day weather data including 15-minute resolution for the next few days."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "minutely_15": "temperature_2m,precipitation,weathercode",
        "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": 14
    }
    response = httpx.get(WEATHER_API_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def main():
    st.set_page_config(page_title="Advanced Weather App", page_icon="🌤️", layout="wide")
    
    st.title("Advanced Weather Dashboard 🌤️")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        city = st.text_input("City", placeholder="e.g. London")
    with col2:
        country = st.text_input("Country (Optional)", placeholder="e.g. United Kingdom")

    if city:
        try:
            with st.spinner(f"Analyzing weather for {city}..."):
                location = get_coordinates(city, country)
                if location:
                    lat, lon = location["latitude"], location["longitude"]
                    weather = get_weather(lat, lon)
                    
                    if weather:
                        tab1, tab2, tab3, tab4 = st.tabs(["Current & Radar", "15-Min Forecast", "14-Day Forecast", "Monthly Overview"])
                        
                        with tab1:
                            st.header(f"{location['name']}, {location.get('country', '')}")
                            c1, c2, c3 = st.columns(3)
                            curr = weather["current_weather"]
                            wmo, emoji = WMO_CODES.get(curr["weathercode"], ("Unknown", "❓"))
                            c1.metric("Temperature", f"{curr['temperature']}°C")
                            c2.metric("Wind Speed", f"{curr['windspeed']} km/h")
                            c3.metric("Condition", f"{emoji} {wmo}")
                            
                            st.subheader("Live Weather Radar")
                            # RainViewer Radar Iframe
                            radar_url = f"https://www.rainviewer.com/map.html?lat={lat}&lon={lon}&zoom=6&type=1&size=512&color=1&tm=1&v=1"
                            components.iframe(radar_url, height=500)
                            st.caption("Radar data provided by RainViewer")

                        with tab2:
                            st.subheader("High-Resolution 15-Minute Forecast")
                            if "minutely_15" in weather:
                                m15 = weather["minutely_15"]
                                df15 = pd.DataFrame({
                                    "Time": pd.to_datetime(m15["time"]),
                                    "Temp (°C)": m15["temperature_2m"],
                                    "Rain (mm)": m15["precipitation"]
                                }).set_index("Time")
                                # Show first 48 hours for clarity
                                st.line_chart(df15.head(48*4)) 
                            else:
                                st.info("15-minute data not available for this location.")

                        with tab3:
                            st.subheader("14-Day Extended Forecast")
                            daily = weather["daily"]
                            df_daily = pd.DataFrame({
                                "Date": pd.to_datetime(daily["time"]),
                                "Max Temp (°C)": daily["temperature_2m_max"],
                                "Min Temp (°C)": daily["temperature_2m_min"],
                                "Rain Chance (%)": daily["precipitation_probability_max"]
                            }).set_index("Date")
                            
                            st.area_chart(df_daily[["Max Temp (°C)", "Min Temp (°C)"]])
                            
                            st.dataframe(df_daily, use_container_width=True)

                        with tab4:
                            # Month view (Current month context for the 14 days)
                            month_name = datetime.now().strftime("%B %Y")
                            st.subheader(f"Overview: {month_name}")
                            
                            # Calendar-like view using columns for the 14 days
                            for i in range(0, 14, 7):
                                cols = st.columns(7)
                                for j in range(7):
                                    idx = i + j
                                    if idx < 14:
                                        with cols[j]:
                                            date_obj = pd.to_datetime(daily["time"][idx])
                                            day_name = date_obj.strftime("%a %d")
                                            w_code = daily["weathercode"][idx]
                                            _, e = WMO_CODES.get(w_code, ("Unknown", "❓"))
                                            st.write(f"**{day_name}**")
                                            st.write(f"{e}")
                                            st.write(f"{daily['temperature_2m_max'][idx]}° / {daily['temperature_2m_min'][idx]}°")
                else:
                    st.warning("Location not found.")
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
