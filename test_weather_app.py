import pytest
import httpx
import urllib.parse
from Weather_app import (
    get_coordinates, 
    get_weather_data, 
    GEOCODING_API_URL, 
    WEATHER_API_URL
)

# --- Geocoding Tests ---

def test_get_coordinates_success(httpx_mock):
    """Test successful coordinate retrieval for a valid city."""
    mock_response = {
        "results": [
            {"name": "Sofia", "latitude": 42.6975, "longitude": 23.3241, "country": "Bulgaria"}
        ]
    }
    httpx_mock.add_response(url=f"{GEOCODING_API_URL}?name=Sofia&count=1&language=en&format=json", json=mock_response)
    
    result = get_coordinates("Sofia")
    assert result is not None
    assert result["name"] == "Sofia"
    assert result["latitude"] == 42.6975

def test_get_coordinates_not_found(httpx_mock):
    """Test behavior when a city is not found."""
    httpx_mock.add_response(url=f"{GEOCODING_API_URL}?name=InvalidCity&count=1&language=en&format=json", json={"results": []})
    result = get_coordinates("InvalidCity")
    assert result is None

def test_get_coordinates_empty_input():
    """Test that empty input returns None immediately."""
    assert get_coordinates("") is None
    assert get_coordinates("   ") is None

# --- Weather Data Tests ---

def test_get_weather_data_full_success(httpx_mock):
    """Test successful retrieval of weather data."""
    mock_f = {
        "current": {"temperature_2m": 15.0, "wind_speed_10m": 5.0, "weather_code": 0},
        "hourly": {
            "time": ["2024-01-01T00:00"] * 24,
            "temperature_2m": [15.0] * 24,
            "relative_humidity_2m": [50] * 24,
            "weather_code": [0] * 24,
            "precipitation_probability": [0] * 24,
            "wind_speed_10m": [5.0] * 24
        },
        "daily": {
            "time": ["2024-01-01"] * 16,
            "temperature_2m_max": [20.0] * 16,
            "temperature_2m_min": [10.0] * 16,
            "weather_code": [0] * 16,
            "precipitation_probability_max": [0] * 16
        }
    }
    lat, lon = 42.6975, 23.3241
    
    f_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
        "hourly": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,precipitation_probability,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,weather_code,precipitation_probability_max,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": 16
    }
    f_qs = urllib.parse.urlencode(f_params)
    httpx_mock.add_response(url=f"{WEATHER_API_URL}?{f_qs}", json=mock_f)
    
    data = get_weather_data(lat, lon)
    assert data is not None
    assert "hourly" in data
    assert len(data["daily"]["time"]) == 16

def test_get_weather_data_failure(httpx_mock):
    """Test that function returns None if API fails."""
    lat, lon = 0.0, 0.0
    # Registering a response that matches the exact URL built by the app
    f_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
        "hourly": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,precipitation_probability,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,weather_code,precipitation_probability_max,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": 16
    }
    f_qs = urllib.parse.urlencode(f_params)
    httpx_mock.add_response(url=f"{WEATHER_API_URL}?{f_qs}", status_code=500)
    
    data = get_weather_data(lat, lon)
    assert data is None
