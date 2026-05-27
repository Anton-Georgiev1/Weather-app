import streamlit as st
import httpx
import pandas as pd
from datetime import datetime

# --- Configuration ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

# Comprehensive WMO Weather interpretation codes (WW)
# https://open-meteo.com/en/docs
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
    if "results" in data and len(data["results"]) > 0:
        return data["results"][0]
    return None

def get_weather(lat: float, lon: float) -> dict | None:
    """Fetch weather data for given coordinates."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "timezone": "auto",
    }
    response = httpx.get(WEATHER_API_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def main():
    st.set_page_config(page_title="Weather App", page_icon="🌤️")
    st.title("Weather App 🌤️")
    st.write("Get real-time weather and 7-day forecast without an API key.")

    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("City", placeholder="e.g. London")
    with col2:
        country = st.text_input("Country (Optional)", placeholder="e.g. United Kingdom")

    if city:
        try:
            with st.spinner(f"Fetching weather for {city}..."):
                location_data = get_coordinates(city, country)
                
                if location_data:
                    lat = location_data.get("latitude")
                    lon = location_data.get("longitude")
                    name = location_data.get("name", city)
                    country_name = location_data.get("country", "")
                    
                    if lat is None or lon is None:
                        st.error("Invalid coordinates received for this location.")
                        return

                    weather_data = get_weather(lat, lon)
                    
                    if weather_data and "current_weather" in weather_data:
                        current = weather_data["current_weather"]
                        code = current.get("weathercode", -1)
                        wmo_desc, emoji = WMO_CODES.get(code, ("Unknown", "❓"))
                        
                        st.header(f"{name}, {country_name}")
                        
                        # Current Weather Metrics
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Temperature", f"{current.get('temperature', 'N/A')}°C")
                        m2.metric("Wind Speed", f"{current.get('windspeed', 'N/A')} km/h")
                        m3.metric("Condition", f"{emoji} {wmo_desc}")
                        
                        # Forecast Chart
                        if "daily" in weather_data:
                            st.subheader("7-Day Temperature Forecast")
                            daily = weather_data["daily"]
                            
                            # Ensure required keys exist in daily
                            if all(k in daily for k in ["time", "temperature_2m_max", "temperature_2m_min"]):
                                df = pd.DataFrame({
                                    "Date": pd.to_datetime(daily["time"]),
                                    "Max Temp (°C)": daily["temperature_2m_max"],
                                    "Min Temp (°C)": daily["temperature_2m_min"]
                                })
                                df.set_index("Date", inplace=True)
                                st.line_chart(df)
                                
                                # Forecast Table
                                with st.expander("Show detailed forecast"):
                                    forecast_details = []
                                    for i in range(len(daily["time"])):
                                        code = daily.get("weathercode", [])[i] if "weathercode" in daily else -1
                                        desc, e = WMO_CODES.get(code, ("Unknown", "❓"))
                                        forecast_details.append({
                                            "Date": daily["time"][i],
                                            "Max (°C)": daily["temperature_2m_max"][i],
                                            "Min (°C)": daily["temperature_2m_min"][i],
                                            "Condition": f"{e} {desc}"
                                        })
                                    st.table(pd.DataFrame(forecast_details))
                            else:
                                st.warning("Forecast data is incomplete.")
                        else:
                            st.warning("Forecast data not available.")
                    else:
                        st.error("Could not fetch current weather data.")
                else:
                    st.warning("City not found. Please check the spelling.")
        except httpx.HTTPStatusError as e:
            st.error(f"API Error: {e.response.status_code}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
