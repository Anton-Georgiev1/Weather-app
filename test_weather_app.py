import pytest
import httpx
from Weather_app import get_coordinates, get_weather_data, GEOCODING_API_URL, WEATHER_API_URL, SEASONAL_API_URL

def test_get_coordinates_success(httpx_mock):
    mock_response = {
        "results": [
            {"name": "Sofia", "latitude": 42.6975, "longitude": 23.3241, "country": "Bulgaria"}
        ]
    }
    httpx_mock.add_response(url=f"{GEOCODING_API_URL}?name=Sofia&count=1&language=en&format=json", json=mock_response)
    
    result = get_coordinates("Sofia")
    assert result is not None
    assert result["name"] == "Sofia"

def test_get_weather_data_success(httpx_mock):
    mock_f = {
        "current_weather": {"temperature": 15.0, "windspeed": 5.0, "weathercode": 0},
        "daily": {
            "time": ["2024-01-01"] * 16,
            "temperature_2m_max": [20.0] * 16,
            "temperature_2m_min": [10.0] * 16,
            "weathercode": [0] * 16,
            "precipitation_probability_max": [0] * 16,
            "precipitation_sum": [0.0] * 16
        }
    }
    mock_s = {
        "daily": {
            "time": ["2024-01-01"] * 30,
            "temperature_2m_max": [21.0] * 30,
            "temperature_2m_min": [11.0] * 30
        }
    }
    lat, lon = 42.6975, 23.3241
    
    # Mock standard API
    f_url = f"{WEATHER_API_URL}?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max%2Ctemperature_2m_min%2Cweathercode%2Cprecipitation_probability_max%2Cprecipitation_sum&timezone=auto&forecast_days=16"
    httpx_mock.add_response(url=f_url, json=mock_f)
    
    # Mock seasonal API
    s_url = f"{SEASONAL_API_URL}?latitude={lat}&longitude={lon}&daily=temperature_2m_max%2Ctemperature_2m_min"
    httpx_mock.add_response(url=s_url, json=mock_s)
    
    f_data, s_data = get_weather_data(lat, lon)
    assert f_data is not None
    assert s_data is not None
    assert len(f_data["daily"]["time"]) == 16
    assert len(s_data["daily"]["time"]) == 30

def test_get_weather_data_seasonal_failure(httpx_mock):
    mock_f = {
        "current_weather": {"temperature": 15.0, "windspeed": 5.0, "weathercode": 0},
        "daily": {
            "time": ["2024-01-01"] * 16,
            "temperature_2m_max": [20.0] * 16,
            "temperature_2m_min": [10.0] * 16,
            "weathercode": [0] * 16,
            "precipitation_probability_max": [0] * 16,
            "precipitation_sum": [0.0] * 16
        }
    }
    lat, lon = 42.6975, 23.3241
    
    # Standard API succeeds
    f_url = f"{WEATHER_API_URL}?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max%2Ctemperature_2m_min%2Cweathercode%2Cprecipitation_probability_max%2Cprecipitation_sum&timezone=auto&forecast_days=16"
    httpx_mock.add_response(url=f_url, json=mock_f)
    
    # Seasonal API fails (e.g. 500)
    s_url = f"{SEASONAL_API_URL}?latitude={lat}&longitude={lon}&daily=temperature_2m_max%2Ctemperature_2m_min"
    httpx_mock.add_response(url=s_url, status_code=500)
    
    f_data, s_data = get_weather_data(lat, lon)
    assert f_data is not None
    assert s_data is None
