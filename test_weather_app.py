import pytest
import httpx
from Weather_app import (
    get_coordinates,
    get_weather_data,
    safe_get,
    get_weather_alerts,
    format_date,
    format_temperature,
    format_wind_speed,
    get_wmo_info,
    generate_hour_card_html,
    generate_day_card_html,
    generate_forecast_row_html,
    generate_alert_html,
    reverse_geocode,
    build_location_from_coordinates,
    GEOCODING_API_URL,
    WEATHER_API_URL,
    REVERSE_GEOCODING_API_URL,
    ALERT_LOOKAHEAD_DAYS
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
    assert "60 km/h" in alerts[1]["message"]

def test_get_weather_alerts_wind_message_converts_to_mph_under_fahrenheit():
    """The wind advisory message must switch to mph under the Fahrenheit toggle,
    not stay locked to km/h regardless of the selected unit."""
    daily_data = {
        "time": ["2024-01-01"],
        "weather_code": [0],
        "precipitation_probability_max": [0],
        "wind_speed_10m_max": [60]
    }
    alerts = get_weather_alerts(daily_data, unit="F")
    assert len(alerts) == 1
    assert "mph" in alerts[0]["message"]
    assert "km/h" not in alerts[0]["message"]

def test_get_weather_alerts_none():
    """Test that no alerts are returned for calm weather."""
    daily_data = {
        "time": ["2024-01-01"],
        "weather_code": [0],
        "precipitation_probability_max": [0],
        "wind_speed_10m_max": [10]
    }
    assert get_weather_alerts(daily_data) == []

def test_get_weather_alerts_respects_lookahead_days():
    """Alerts only look ALERT_LOOKAHEAD_DAYS ahead: a severe day on the last day
    inside the window must trigger, and the same day one slot later must not."""
    time_series = [f"2024-01-{day:02d}" for day in range(1, ALERT_LOOKAHEAD_DAYS + 2)]

    weather_code_inside_window = [0] * (ALERT_LOOKAHEAD_DAYS + 1)
    weather_code_inside_window[ALERT_LOOKAHEAD_DAYS - 1] = 95  # last day inside the window
    daily_data_inside = {
        "time": time_series,
        "weather_code": weather_code_inside_window,
        "precipitation_probability_max": [80] * (ALERT_LOOKAHEAD_DAYS + 1),
        "wind_speed_10m_max": [0] * (ALERT_LOOKAHEAD_DAYS + 1)
    }
    assert len(get_weather_alerts(daily_data_inside)) == 1

    weather_code_outside_window = [0] * (ALERT_LOOKAHEAD_DAYS + 1)
    weather_code_outside_window[ALERT_LOOKAHEAD_DAYS] = 95  # first day outside the window
    daily_data_outside = {
        "time": time_series,
        "weather_code": weather_code_outside_window,
        "precipitation_probability_max": [80] * (ALERT_LOOKAHEAD_DAYS + 1),
        "wind_speed_10m_max": [0] * (ALERT_LOOKAHEAD_DAYS + 1)
    }
    assert get_weather_alerts(daily_data_outside) == []

def test_format_temperature():
    """Test Celsius passthrough, Fahrenheit conversion, and missing-value fallback."""
    assert format_temperature(20.0, "C") == "20.0°C"
    assert format_temperature(20.0, "F") == "68.0°F"
    assert format_temperature(None, "C") == "--°C"
    assert format_temperature(None, "F") == "--°F"

def test_format_wind_speed():
    """Test km/h passthrough (localized unit label), mph conversion under the
    Fahrenheit toggle, and missing-value fallback."""
    assert format_wind_speed(10.0, "C", "en") == "10.0 km/h"
    assert format_wind_speed(10.0, "C", "bg") == "10.0 км/ч"
    assert format_wind_speed(10.0, "F") == "6.2 mph"
    assert format_wind_speed(None, "C", "en") == "-- km/h"
    assert format_wind_speed(None, "F") == "-- mph"

def test_generate_hour_card_html_smoke():
    """Smoke test for the 24h-strip hour card, including the weather-icon tooltip."""
    result = generate_hour_card_html("2024-01-01T14:00", 0, 10, 20.0)
    assert "hour-card" in result
    assert "title='Clear sky'" in result
    assert "20.0°C" in result

def test_generate_day_card_html_smoke():
    """Smoke test for the 7-day card, including the rain/wind tooltip text."""
    result = generate_day_card_html("2024-01-01", 0, 10, wind=15.0, max_t=20.0, min_t=10.0)
    assert "day-card" in result
    assert "title='Rain chance'" in result
    assert "title='Wind'" in result

def test_generate_day_card_html_wind_converts_to_mph_under_fahrenheit():
    """Wind speed must follow the temperature unit toggle, not stay locked to km/h."""
    result_metric = generate_day_card_html("2024-01-01", 0, 10, wind=16.0934, max_t=20.0, min_t=10.0, unit="C")
    assert "💨 16<" in result_metric

    result_imperial = generate_day_card_html("2024-01-01", 0, 10, wind=16.0934, max_t=20.0, min_t=10.0, unit="F")
    assert "💨 10<" in result_imperial  # 16.0934 km/h ≈ 10 mph

def test_generate_forecast_row_html_smoke():
    """Smoke test for the 14-day compact row, including the rain/wind tooltip text."""
    result = generate_forecast_row_html("2024-01-01", 0, 10, wind=15.0, max_t=20.0, min_t=10.0)
    assert "row-14" in result
    assert "title='Rain chance'" in result
    assert "title='Wind'" in result

def test_generate_forecast_row_html_wind_converts_to_mph_under_fahrenheit():
    """Wind speed in the 14-day row must switch to mph under the Fahrenheit toggle."""
    result = generate_forecast_row_html("2024-01-01", 0, 10, wind=16.0934, max_t=20.0, min_t=10.0, unit="F")
    assert "10.0 mph" in result  # 16.0934 km/h ≈ 10 mph

def test_generate_alert_html():
    """Test the alert banner carries the icon, message, and a localized tooltip."""
    result = generate_alert_html("⚠️", "Storm incoming", lang="en")
    assert "⚠️" in result
    assert "Storm incoming" in result
    assert "title='Severe Weather'" in result

    result_bg = generate_alert_html("⚠️", "Идва буря", lang="bg")
    assert "title='Опасно време'" in result_bg

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
    # Deliberately passing the wrong type to exercise safe_get's runtime isinstance guard,
    # which protects against malformed API responses regardless of the declared type.
    assert safe_get([1, 2, 3], "temp", 0) is None  # pyright: ignore[reportArgumentType]

def test_safe_get_none_element():
    """Test safe_get when the element at index is None."""
    data = {"temp": [10, None, 30]}
    assert safe_get(data, "temp", 1, default=15) == 15

# --- Bulgarian Translation & Date Formatting Tests ---

def test_format_date_bg():
    """Test that dates are correctly formatted and localized to Bulgarian."""
    # 2024-06-01 is a Saturday
    bg_alert_date = format_date("2024-06-01", "%A, %B %d", "bg")
    assert "Събота" in bg_alert_date
    assert "Юни" in bg_alert_date
    
    bg_card_date = format_date("2024-06-01", "%A, %d %b", "bg")
    assert "Събота" in bg_card_date
    assert "Юни" in bg_card_date

def test_format_date_empty_or_none():
    """pd.to_datetime doesn't raise for '' or None, it returns NaT, whose strftime()
    raises ValueError. format_date must catch this itself rather than crash."""
    assert format_date("", "%A, %d %b", "en") == ""
    assert format_date(None, "%A, %d %b", "en") == "None"  # pyright: ignore[reportArgumentType]

def test_get_weather_alerts_with_missing_date():
    """A malformed/missing entry in daily['time'] must not crash alert generation."""
    daily_data = {
        "time": ["", "2024-01-02"],
        "weather_code": [95, 0],
        "precipitation_probability_max": [80, 0],
        "wind_speed_10m_max": [10, 60]
    }
    alerts = get_weather_alerts(daily_data)
    assert len(alerts) == 2

def test_get_wmo_info_bg():
    """Test retrieving WMO condition and emoji in Bulgarian."""
    desc, emoji = get_wmo_info(0, "bg")
    assert desc == "Ясно небе"
    assert emoji == "☀️"
    
    desc_ts, emoji_ts = get_wmo_info(95, "bg")
    assert desc_ts == "Гръмотевична буря"
    assert emoji_ts == "⛈️"

def test_get_weather_alerts_bg():
    """Test weather alerts generated in Bulgarian."""
    daily_data = {
        "time": ["2024-06-01", "2024-06-02"],
        "weather_code": [95, 0],
        "precipitation_probability_max": [85, 0],
        "wind_speed_10m_max": [10, 55]
    }
    alerts = get_weather_alerts(daily_data, lang="bg")
    assert len(alerts) == 2
    assert "Гръмотевична буря" in alerts[0]["message"]
    assert "Предупреждение за вятър" in alerts[1]["message"]
    assert "85%" in alerts[0]["message"]
    assert "55 км/ч" in alerts[1]["message"]

# --- Geocoding Tests ---

def test_get_coordinates_success(httpx_mock):
    """Test successful coordinate retrieval for a valid city."""
    mock_response = {
        "results": [
            {"name": "Sofia", "latitude": 42.6975, "longitude": 23.3241, "country": "Bulgaria"}
        ]
    }
    httpx_mock.add_response(json=mock_response)
    
    result = get_coordinates("Sofia")
    assert result is not None
    assert result["name"] == "Sofia"
    assert result["latitude"] == 42.6975
    
    # Assert the correct URL was dynamically built and called
    request = httpx_mock.get_request()
    assert request is not None
    assert str(request.url).startswith(GEOCODING_API_URL)
    assert "name=Sofia" in str(request.url)

def test_get_coordinates_with_country(httpx_mock):
    """Test coordinate retrieval when city and country are provided."""
    mock_response = {
        "results": [
            {"name": "Paris", "latitude": 48.8566, "longitude": 2.3522, "country": "France"}
        ]
    }
    httpx_mock.add_response(json=mock_response)
    
    result = get_coordinates("Paris", "France")
    assert result is not None
    assert result["name"] == "Paris"
    assert result["country"] == "France"

    # Assert that both City and Country were encoded into the URL correctly
    request = httpx_mock.get_request()
    assert "Paris" in str(request.url)
    assert "France" in str(request.url)

def test_get_coordinates_falls_back_to_other_language(httpx_mock):
    """A Cyrillic city name isn't matched under language=en, but is under language=bg;
    the default-language (en) search should fall back and still find it."""
    httpx_mock.add_response(json={"results": []})
    httpx_mock.add_response(json={
        "results": [
            {"name": "Ямбол", "latitude": 42.4833, "longitude": 26.5, "country": "Bulgaria"}
        ]
    })

    result = get_coordinates("Ямбол")
    assert result is not None
    assert result["name"] == "Ямбол"

    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert "language=en" in str(requests[0].url)
    assert "language=bg" in str(requests[1].url)

def test_get_coordinates_uses_current_ui_language_first(httpx_mock):
    """When the UI is already in Bulgarian, the Bulgarian-language search should be
    tried first rather than only as a fallback."""
    mock_response = {
        "results": [
            {"name": "Ямбол", "latitude": 42.4833, "longitude": 26.5, "country": "Bulgaria"}
        ]
    }
    httpx_mock.add_response(json=mock_response)

    result = get_coordinates("Ямбол", lang="bg")
    assert result is not None

    request = httpx_mock.get_request()
    assert request is not None
    assert "language=bg" in str(request.url)

def test_get_coordinates_not_found(httpx_mock):
    """Test behavior when a city is not found in any of the retried languages."""
    httpx_mock.add_response(json={"results": []}, is_reusable=True)
    result = get_coordinates("InvalidCity")
    assert result is None

def test_get_coordinates_empty_input():
    """Test that empty input returns None immediately without firing API."""
    assert get_coordinates("") is None
    assert get_coordinates("   ") is None

def test_get_coordinates_exception(httpx_mock):
    """Test that function handles timeouts and network crashes gracefully across retries."""
    httpx_mock.add_exception(httpx.TimeoutException("Timeout"), is_reusable=True)
    result = get_coordinates("AnyCity")
    assert result is None

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
    httpx_mock.add_response(json=mock_f)
    
    data = get_weather_data(lat, lon)
    assert data is not None
    assert "hourly" in data
    assert len(data["daily"]["time"]) == 16
    
    # Assert parameters were correctly bound to the API fetch URL
    request = httpx_mock.get_request()
    assert str(request.url).startswith(WEATHER_API_URL)
    assert f"latitude={lat}" in str(request.url)
    assert f"longitude={lon}" in str(request.url)

def test_get_weather_data_failure(httpx_mock):
    """Test that function handles API 500 error codes correctly."""
    lat, lon = 0.0, 0.0
    httpx_mock.add_response(status_code=500)

    data = get_weather_data(lat, lon)
    assert data is None

# --- Reverse Geocoding Tests ---

def test_reverse_geocode_success(httpx_mock):
    """Test successful reverse geocoding with a city in the address."""
    mock_response = {"address": {"city": "Sofia", "country": "Bulgaria"}}
    httpx_mock.add_response(json=mock_response)

    result = reverse_geocode(42.6975, 23.3241)
    assert result == {"name": "Sofia", "country": "Bulgaria"}

    request = httpx_mock.get_request()
    assert str(request.url).startswith(REVERSE_GEOCODING_API_URL)

def test_reverse_geocode_uses_requested_language(httpx_mock):
    """Test that the UI language is forwarded to Nominatim so results are localized consistently
    with the forward-geocoding path (which always requests language=en)."""
    mock_response = {"address": {"city": "Sofia", "country": "Bulgaria"}}
    httpx_mock.add_response(json=mock_response)

    reverse_geocode(42.6975, 23.3241, lang="bg")

    request = httpx_mock.get_request()
    assert "accept-language=bg" in str(request.url)

def test_reverse_geocode_town_fallback(httpx_mock):
    """Test that 'town' is used when 'city' is absent from the address."""
    mock_response = {"address": {"town": "Bansko", "country": "Bulgaria"}}
    httpx_mock.add_response(json=mock_response)

    result = reverse_geocode(41.8383, 23.4880)
    assert result == {"name": "Bansko", "country": "Bulgaria"}

def test_reverse_geocode_missing_country(httpx_mock):
    """Test that a missing country in the address results in None."""
    mock_response = {"address": {"city": "Sofia"}}
    httpx_mock.add_response(json=mock_response)

    result = reverse_geocode(42.6975, 23.3241)
    assert result is None

def test_reverse_geocode_rural_coordinates_keep_known_country(httpx_mock):
    """Rural coordinates can resolve to a country with no city/town/village/county;
    the known country must still be surfaced instead of being discarded entirely."""
    mock_response = {"address": {"country": "France"}}
    httpx_mock.add_response(json=mock_response)

    result = reverse_geocode(46.6, 2.5)
    assert result == {"name": "", "country": "France"}

def test_reverse_geocode_no_address(httpx_mock):
    """Test behavior when coordinates resolve to no address data (e.g. open ocean)."""
    httpx_mock.add_response(json={})
    result = reverse_geocode(0.0, 0.0)
    assert result is None

def test_reverse_geocode_exception(httpx_mock):
    """Test that function handles timeouts and network crashes gracefully."""
    httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
    result = reverse_geocode(42.6975, 23.3241)
    assert result is None

def test_build_location_from_coordinates_success(httpx_mock):
    """Test that a resolved place name and country are used when reverse geocoding succeeds."""
    mock_response = {"address": {"city": "Sofia", "country": "Bulgaria"}}
    httpx_mock.add_response(json=mock_response)

    location = build_location_from_coordinates(42.6975, 23.3241, lang="en")
    assert location == {
        "name": "Sofia",
        "country": "Bulgaria",
        "latitude": 42.6975,
        "longitude": 23.3241
    }

def test_build_location_from_coordinates_rural_keeps_known_country(httpx_mock):
    """Rural coordinates with a known country but no city/town/village/county must show
    the generic place name alongside the real country, not lose the country entirely."""
    mock_response = {"address": {"country": "France"}}
    httpx_mock.add_response(json=mock_response)

    location = build_location_from_coordinates(46.6, 2.5, lang="en")
    assert location["name"] == "Your Current Location"
    assert location["country"] == "France"

def test_build_location_from_coordinates_fallback(httpx_mock):
    """Test the generic fallback location when reverse geocoding fails."""
    httpx_mock.add_response(json={})

    location = build_location_from_coordinates(0.0, 0.0, lang="en")
    assert location["name"] == "Your Current Location"
    assert location["country"] == ""
    assert location["latitude"] == 0.0
    assert location["longitude"] == 0.0

def test_build_location_from_coordinates_fallback_bg(httpx_mock):
    """Test the generic fallback location is translated to Bulgarian."""
    httpx_mock.add_response(json={})

    location = build_location_from_coordinates(0.0, 0.0, lang="bg")
    assert location["name"] == "Текущото ви местоположение"
    assert location["country"] == ""