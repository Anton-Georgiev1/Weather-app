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
    assert result["latitude"] == 51.50853

def test_get_coordinates_no_results(httpx_mock):
    httpx_mock.add_response(url=f"{GEOCODING_API_URL}?name=NonExistentCity&count=1&language=en&format=json", json={"results": []})
    
    result = get_coordinates("NonExistentCity")
    assert result is None

def test_get_coordinates_empty_input():
    assert get_coordinates("") is None
    assert get_coordinates("   ") is None

def test_get_weather_success(httpx_mock):
    mock_weather = {
        "current_weather": {"temperature": 20.0, "windspeed": 10.0, "weathercode": 0},
        "daily": {
            "time": ["2024-01-01"],
            "temperature_2m_max": [22.0],
            "temperature_2m_min": [18.0],
            "weathercode": [0]
        }
    }
    lat, lon = 51.50853, -0.12574
    httpx_mock.add_response(url=f"{WEATHER_API_URL}?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max%2Ctemperature_2m_min%2Cweathercode&timezone=auto", json=mock_weather)
    
    result = get_weather(lat, lon)
    assert result is not None
    assert result["current_weather"]["temperature"] == 20.0
    assert "daily" in result

def test_get_coordinates_special_characters(httpx_mock):
    mock_response = {
        "results": [
            {"name": "São Paulo", "latitude": -23.55, "longitude": -46.63, "country": "Brazil"}
        ]
    }
    httpx_mock.add_response(url=f"{GEOCODING_API_URL}?name=S%C3%A3o+Paulo&count=1&language=en&format=json", json=mock_response)
    
    result = get_coordinates("São Paulo")
    assert result is not None
    assert result["name"] == "São Paulo"

def test_get_weather_api_error(httpx_mock):
    lat, lon = 51.5, -0.1
    httpx_mock.add_response(status_code=500)
    
    with pytest.raises(httpx.HTTPStatusError):
        get_weather(lat, lon)

def test_get_coordinates_api_error(httpx_mock):
    httpx_mock.add_response(status_code=404)
    
    with pytest.raises(httpx.HTTPStatusError):
        get_coordinates("London")
