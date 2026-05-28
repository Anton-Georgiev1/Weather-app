import pytest
import httpx
import urllib.parse
from Weather_app import (
    get_coordinates, 
    get_weather_data, 
    safe_get,
    calculate_daily_average_humidity,
    get_weather_alerts,
    generate_forecast_card_html,
    GEOCODING_API_URL, 
    WEATHER_API_URL
)

# --- Utility Tests ---

def test_get_weather_alerts():
    """Test alert logic for severe weather and high winds."""
    daily_data = {
        "time": ["2024-01-01", "2024-01-02"],
        "weather_code": [95, 0], # 95 is Thunderstorm
        "precipitation_probability_max": [80, 0],
        "wind_speed_10m_max": [10, 60] # 60 is high wind
    }
    alerts = get_weather_alerts(daily_data)
    assert len(alerts) == 2
    assert "Thunderstorm" in alerts[0]["message"]
    assert "Wind Advisory" in alerts[1]["message"]

def test_get_weather_alerts_none():
    """Test that no alerts are returned for calm weather."""
    daily_data = {
        "time": ["2024-01-01"],
        "weather_code": [0],
        "precipitation_probability_max": [0],
        "wind_speed_10m_max": [10]
    }
    assert get_weather_alerts(daily_data) == []

def test_generate_forecast_card_html_smoke():
    """Smoke test for HTML generation to ensure no crashes."""
    html = generate_forecast_card_html(
        "2024-01-01T12:00", 0, 10, wind=5, humidity=50, max_t=20, min_t=10
    )
    assert "forecast-card" in html
    assert "Clear sky" in html
    assert "20°" in html

def test_calculate_daily_average_humidity():
    """Test average calculation for complete and partial days."""
    # 24 hours of 50% humidity
    data = [50.0] * 24 + [60.0] * 24
    result = calculate_daily_average_humidity(data)
    assert result == [50.0, 60.0]

def test_calculate_daily_average_humidity_with_nones():
    """Test average calculation with missing values."""
    data = [50.0, None, 50.0] + [None] * 21 # First day: (50+50)/2 = 50.0
    result = calculate_daily_average_humidity(data)
    assert result == [50.0]

def test_calculate_daily_average_humidity_empty():
    """Test average calculation with empty or all-None data."""
    assert calculate_daily_average_humidity([]) == []
    assert calculate_daily_average_humidity([None] * 24) == [None]

def test_safe_get_valid():
    """Test safe_get with valid data and index."""
    data = {"temp": [10, 20, 30]}
    assert safe_get(data, "temp", 1) == 20

def test_safe_get_invalid_index():
    """Test safe_get with an index out of bounds."""
    data = {"temp": [10, 20]}
    assert safe_get(data, "temp", 5, default="N/A") == "N/A"

def test_safe_get_missing_key():
    """Test safe_get with a missing key."""
    data = {"temp": [10]}
    assert safe_get(data, "humidity", 0, default=0) == 0

def test_safe_get_not_a_dict():
    """Test safe_get when input is not a dictionary."""
    assert safe_get(None, "temp", 0) is None
    assert safe_get([1, 2, 3], "temp", 0) is None

def test_safe_get_none_element():
    """Test safe_get when the element at index is None."""
    data = {"temp": [10, None, 30]}
    assert safe_get(data, "temp", 1, default=15) == 15

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

def test_get_coordinates_with_country(httpx_mock):
    """Test coordinate retrieval when city and country are provided."""
    mock_response = {
        "results": [
            {"name": "Paris", "latitude": 48.8566, "longitude": 2.3522, "country": "France"}
        ]
    }
    # Open-Meteo appends country to query like "Paris, France"
    httpx_mock.add_response(url=f"{GEOCODING_API_URL}?name=Paris%2C+France&count=1&language=en&format=json", json=mock_response)
    
    result = get_coordinates("Paris", "France")
    assert result is not None
    assert result["name"] == "Paris"
    assert result["country"] == "France"

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

def test_get_coordinates_exception(httpx_mock):
    """Test that function returns None when an exception occurs."""
    httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
    result = get_coordinates("AnyCity")
    assert result is None

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
