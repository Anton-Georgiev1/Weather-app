import pytest
import httpx
from Weather_app import get_coordinates, get_weather, GEOCODING_API_URL, WEATHER_API_URL

def test_get_coordinates_success(httpx_mock):
    mock_response = {
        "results": [
            {"name": "London", "latitude": 51.50853, "longitude": -0.12574, "country": "United Kingdom"}
        ]
    }
    httpx_mock.add_response(url=f"{GEOCODING_API_URL}?name=London&count=1&language=en&format=json", json=mock_response)
    
    result = get_coordinates("London")
    assert result is not None
    assert result["name"] == "London"

def test_get_weather_success(httpx_mock):
    mock_weather = {
        "current_weather": {"temperature": 20.0, "windspeed": 10.0, "weathercode": 0},
        "daily": {
            "time": ["2024-01-01"] * 14,
            "temperature_2m_max": [22.0] * 14,
            "temperature_2m_min": [18.0] * 14,
            "weathercode": [0] * 14,
            "precipitation_probability_max": [10] * 14
        },
        "minutely_15": {
            "time": ["2024-01-01T00:00"] * 96,
            "temperature_2m": [20.0] * 96,
            "precipitation": [0.0] * 96,
            "weathercode": [0] * 96
        }
    }
    lat, lon = 51.5, -0.1
    # Match updated query with forecast_days=14 and minutely_15
    url_pattern = f"{WEATHER_API_URL}?latitude={lat}&longitude={lon}&current_weather=true&minutely_15=temperature_2m%2Cprecipitation%2Cweathercode&daily=temperature_2m_max%2Ctemperature_2m_min%2Cweathercode%2Cprecipitation_probability_max&timezone=auto&forecast_days=14"
    httpx_mock.add_response(url=url_pattern, json=mock_weather)
    
    result = get_weather(lat, lon)
    assert result is not None
    assert len(result["daily"]["time"]) == 14
    assert "minutely_15" in result

def test_get_weather_api_error(httpx_mock):
    lat, lon = 51.5, -0.1
    httpx_mock.add_response(status_code=500)
    with pytest.raises(httpx.HTTPStatusError):
        get_weather(lat, lon)
