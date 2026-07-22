import httpx

from weather_app.alerts import (
    ALERT_LOOKAHEAD_DAYS,
    DAY_CARD_STORM_CODES,
    DAY_CARD_STORM_SEVERE_CODES,
    get_near_term_alerts,
    get_weather_alerts,
    near_term_storm_is_today,
    summarize_segment_risk,
)
from weather_app.config import GEOCODING_API_URL, REVERSE_GEOCODING_API_URL, WEATHER_API_URL
from weather_app.formatting import format_date, format_temperature, format_wind_speed, get_time_of_day_segment, get_wmo_info, safe_get
from weather_app.render import generate_alert_html, generate_day_card_html, generate_forecast_row_html, generate_hour_card_html, generate_segment_risk_html
from weather_app.weather_api import build_location_from_coordinates, get_coordinates, get_weather_data, reverse_geocode


# --- Utility Tests ---


def test_get_weather_alerts():
    """Test alert logic for severe weather and high winds."""
    daily_data = {
        "time": ["2024-01-01", "2024-01-02"],
        "weather_code": [95, 0],  # 95 is Thunderstorm
        "precipitation_probability_max": [80, 0],
        "wind_speed_10m_max": [10, 60]  # 60 is high wind
    }
    alerts = get_weather_alerts(daily_data)
    assert len(alerts) == 2
    assert "Thunderstorm" in alerts[0]["message"]
    assert "Wind Advisory" in alerts[1]["message"]
    assert "60 km/h" in alerts[1]["message"]


def test_get_weather_alerts_wind_message_converts_to_mph_under_fahrenheit():
    """The wind advisory message must switch to mph under the Fahrenheit
    toggle, not stay locked to km/h regardless of the selected unit."""
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


def test_get_weather_alerts_skip_today_precip_drops_only_todays_condition_alert():
    """skip_today_precip=True must drop today's severe-condition alert (it's
    a duplicate of an already-raised near-term alert) but keep today's wind
    alert and every future day's alerts untouched."""
    daily_data = {
        "time": ["2024-01-01", "2024-01-02"],
        "weather_code": [95, 99],  # both severe
        "precipitation_probability_max": [80, 90],
        "wind_speed_10m_max": [60, 10]  # today also has high wind
    }
    alerts = get_weather_alerts(daily_data, skip_today_precip=True)
    assert len(alerts) == 2
    assert "Wind Advisory" in alerts[0]["message"]  # today's wind alert survives
    assert "Severe Thunderstorm" in alerts[1]["message"]  # tomorrow's condition alert survives
    assert not any("Thunderstorm" in a["message"] and "Severe" not in a["message"] for a in alerts)


def test_get_weather_alerts_skip_today_precip_false_keeps_default_behavior():
    """The default (skip_today_precip=False) must be unaffected, so existing
    callers that don't pass the flag keep seeing today's condition alert."""
    daily_data = {
        "time": ["2024-01-01"],
        "weather_code": [95],
        "precipitation_probability_max": [80],
        "wind_speed_10m_max": [10]
    }
    alerts = get_weather_alerts(daily_data)
    assert len(alerts) == 1
    assert "Thunderstorm" in alerts[0]["message"]


def test_get_weather_alerts_drops_todays_precip_alert_once_storm_has_passed():
    """When hourly_data/upcoming_start_idx are supplied, today's severe-weather
    alert must disappear once every remaining hour today has clear conditions --
    it shouldn't linger just because the daily forecast still lists a storm code
    for the day as a whole."""
    daily_data = {
        "time": ["2024-01-01", "2024-01-02"],
        "weather_code": [95, 0],
        "precipitation_probability_max": [80, 0],
        "wind_speed_10m_max": [10, 10]
    }
    hourly_data = {
        "time": [f"2024-01-01T{h:02d}:00" for h in range(24)],
        "weather_code": [95] * 18 + [0] * 6,  # storm passed by 18:00
    }
    alerts = get_weather_alerts(daily_data, hourly_data=hourly_data, upcoming_start_idx=20)
    assert not any("Thunderstorm" in a["message"] for a in alerts)


def test_get_weather_alerts_keeps_todays_precip_alert_while_storm_still_ahead():
    """The same today's-alert check must NOT drop the alert while a storm hour
    still remains later today."""
    daily_data = {
        "time": ["2024-01-01"],
        "weather_code": [95],
        "precipitation_probability_max": [80],
        "wind_speed_10m_max": [10]
    }
    hourly_data = {
        "time": [f"2024-01-01T{h:02d}:00" for h in range(24)],
        "weather_code": [0] * 18 + [95] * 6,  # storm arrives later today
    }
    alerts = get_weather_alerts(daily_data, hourly_data=hourly_data, upcoming_start_idx=10)
    assert any("Thunderstorm" in a["message"] for a in alerts)


def test_get_weather_alerts_without_hourly_data_keeps_default_behavior():
    """Callers that don't pass hourly_data (e.g. existing tests above) must keep
    seeing today's alert regardless of time of day."""
    daily_data = {
        "time": ["2024-01-01"],
        "weather_code": [95],
        "precipitation_probability_max": [80],
        "wind_speed_10m_max": [10]
    }
    alerts = get_weather_alerts(daily_data, upcoming_start_idx=23)
    assert any("Thunderstorm" in a["message"] for a in alerts)


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
    """Alerts only look ALERT_LOOKAHEAD_DAYS ahead: a severe day on the
    last day inside the window must trigger, and the same day one slot
    later must not."""
    time_series = [
        f"2024-01-{day:02d}"
        for day in range(1, ALERT_LOOKAHEAD_DAYS + 2)
    ]

    weather_code_inside_window = [0] * (ALERT_LOOKAHEAD_DAYS + 1)
    # last day inside the window:
    weather_code_inside_window[ALERT_LOOKAHEAD_DAYS - 1] = 95
    daily_data_inside = {
        "time": time_series,
        "weather_code": weather_code_inside_window,
        "precipitation_probability_max": [80] * (ALERT_LOOKAHEAD_DAYS + 1),
        "wind_speed_10m_max": [0] * (ALERT_LOOKAHEAD_DAYS + 1)
    }
    assert len(get_weather_alerts(daily_data_inside)) == 1

    weather_code_outside_window = [0] * (ALERT_LOOKAHEAD_DAYS + 1)
    # first day outside the window:
    weather_code_outside_window[ALERT_LOOKAHEAD_DAYS] = 95
    daily_data_outside = {
        "time": time_series,
        "weather_code": weather_code_outside_window,
        "precipitation_probability_max": [80] * (ALERT_LOOKAHEAD_DAYS + 1),
        "wind_speed_10m_max": [0] * (ALERT_LOOKAHEAD_DAYS + 1)
    }
    assert get_weather_alerts(daily_data_outside) == []


def test_get_near_term_alerts_none_when_clear():
    """No alert when both the current and next hour are clear."""
    hourly_data = {
        "time": ["2024-01-01T10:00", "2024-01-01T11:00"],
        "weather_code": [0, 1],
        "precipitation_probability": [10, 20]
    }
    assert get_near_term_alerts(hourly_data, 0) == []


def test_get_near_term_alerts_rain_code_warning():
    """A rain code in the checked window produces a warning-severity alert."""
    hourly_data = {
        "time": ["2024-01-01T10:00", "2024-01-01T11:00"],
        "weather_code": [61, 0],  # 61 = Rain: Slight
        "precipitation_probability": [50, 10]
    }
    alerts = get_near_term_alerts(hourly_data, 0)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "warning"
    assert "Rain: Slight" in alerts[0]["message"]


def test_get_near_term_alerts_storm_code_error():
    """A thunderstorm code in the checked window produces an
    error-severity alert."""
    hourly_data = {
        "time": ["2024-01-01T10:00", "2024-01-01T11:00"],
        "weather_code": [0, 95],  # 95 = Thunderstorm
        "precipitation_probability": [10, 90]
    }
    alerts = get_near_term_alerts(hourly_data, 0)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "error"
    assert "Thunderstorm" in alerts[0]["message"]


def test_get_near_term_alerts_probability_only_trigger():
    """A clear weather_code with a high enough precipitation_probability
    still warns, but must not borrow "Clear sky" as the condition text --
    that would render as the self-contradicting "Clear sky expected...
    (85% chance of precipitation)"."""
    hourly_data = {
        "time": ["2024-01-01T10:00", "2024-01-01T11:00"],
        "weather_code": [0, 0],
        "precipitation_probability": [85, 10]
    }
    alerts = get_near_term_alerts(hourly_data, 0)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "warning"
    assert "Clear sky" not in alerts[0]["message"]
    assert "Rain" in alerts[0]["message"]


def test_get_near_term_alerts_storm_beats_earlier_warning():
    """A storm in the next hour outranks a plain rain warning this hour."""
    hourly_data = {
        "time": ["2024-01-01T10:00", "2024-01-01T11:00"],
        "weather_code": [61, 95],
        "precipitation_probability": [50, 90]
    }
    alerts = get_near_term_alerts(hourly_data, 0)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "error"


def test_get_near_term_alerts_tie_keeps_sooner_hour():
    """When both checked hours are the same severity, the sooner hour's
    condition wins."""
    hourly_data = {
        "time": ["2024-01-01T10:00", "2024-01-01T11:00"],
        "weather_code": [95, 96],  # both storm-tier
        "precipitation_probability": [90, 90]
    }
    alerts = get_near_term_alerts(hourly_data, 0)
    assert len(alerts) == 1
    assert "Thunderstorm" in alerts[0]["message"]


def test_get_near_term_alerts_out_of_range_index():
    """An upcoming_start_idx past the end of the array yields no alert,
    no exception."""
    hourly_data = {
        "time": ["2024-01-01T10:00"],
        "weather_code": [95],
        "precipitation_probability": [90]
    }
    assert get_near_term_alerts(hourly_data, 5) == []


def test_get_near_term_alerts_empty_data():
    """Missing or empty hourly data yields no alert, no exception."""
    assert get_near_term_alerts({}, 0) == []
    assert get_near_term_alerts(None, 0) == []  # pyright: ignore[reportArgumentType]


def test_get_near_term_alerts_date_matches_triggering_hour():
    """The returned alert's date must be the triggering hour's own date, not
    always "today" -- this is what lets callers avoid conflating a storm at
    23:00 today with one at 00:00 tomorrow."""
    hourly_data = {
        "time": ["2024-01-01T23:00", "2024-01-02T00:00"],
        "weather_code": [1, 95],  # storm only in tomorrow's first hour
        "precipitation_probability": [10, 90]
    }
    alerts = get_near_term_alerts(hourly_data, 0)
    assert len(alerts) == 1
    assert alerts[0]["date"] == "2024-01-02"


def test_near_term_storm_is_today_true_when_triggering_hour_matches_today():
    near_term_alerts = [{"severity": "error", "message": "x", "date": "2024-01-01"}]
    daily_data = {"time": ["2024-01-01", "2024-01-02"]}
    assert near_term_storm_is_today(near_term_alerts, daily_data) is True


def test_near_term_storm_is_today_false_across_midnight_boundary():
    """A near-term storm whose triggering hour is actually tomorrow (e.g.
    checked at 23:00) must not count as "today's" storm -- otherwise
    get_weather_alerts would wrongly drop today's own, distinct alert."""
    near_term_alerts = [{"severity": "error", "message": "x", "date": "2024-01-02"}]
    daily_data = {"time": ["2024-01-01", "2024-01-02"]}
    assert near_term_storm_is_today(near_term_alerts, daily_data) is False


def test_near_term_storm_is_today_false_when_no_error_severity():
    near_term_alerts = [{"severity": "warning", "message": "x", "date": "2024-01-01"}]
    daily_data = {"time": ["2024-01-01"]}
    assert near_term_storm_is_today(near_term_alerts, daily_data) is False


def test_near_term_storm_is_today_false_on_missing_daily_data():
    near_term_alerts = [{"severity": "error", "message": "x", "date": "2024-01-01"}]
    assert near_term_storm_is_today(near_term_alerts, {}) is False
    assert near_term_storm_is_today(near_term_alerts, None) is False


def test_summarize_segment_risk_low_probability_is_not_danger():
    hourly_data = {
        "precipitation_probability": [10, 20, 30],
        "weather_code": [0, 1, 2],
    }
    result = summarize_segment_risk(hourly_data, [0, 1, 2])
    assert result == {"max_prob": 30, "has_storm": False, "is_danger": False}


def test_summarize_segment_risk_high_probability_is_danger():
    hourly_data = {
        "precipitation_probability": [10, 85, 30],
        "weather_code": [0, 61, 2],
    }
    result = summarize_segment_risk(hourly_data, [0, 1, 2])
    assert result == {"max_prob": 85, "has_storm": False, "is_danger": True}


def test_summarize_segment_risk_storm_code_is_danger_even_at_low_probability():
    hourly_data = {
        "precipitation_probability": [5, 10],
        "weather_code": [95, 0],
    }
    result = summarize_segment_risk(hourly_data, [0, 1])
    assert result == {"max_prob": 10, "has_storm": True, "is_danger": True}


def test_summarize_segment_risk_empty_indices():
    hourly_data = {"precipitation_probability": [50], "weather_code": [95]}
    assert summarize_segment_risk(hourly_data, []) == {"max_prob": 0, "has_storm": False, "is_danger": False}


def test_generate_segment_risk_html_danger_uses_alert_error_class():
    html = generate_segment_risk_html(85, has_storm=True, is_danger=True, lang="en")
    assert "alert-error" in html
    assert "85%" in html
    assert "⛈️" in html


def test_generate_segment_risk_html_safe_range_omits_danger_class():
    html = generate_segment_risk_html(20, has_storm=False, is_danger=False, lang="en")
    assert "alert-error" not in html
    assert "20%" in html
    assert "💧" in html


def test_generate_segment_risk_html_probability_only_danger_uses_alert_error_class():
    html = generate_segment_risk_html(85, has_storm=False, is_danger=True, lang="en")
    assert "alert-error" in html
    assert "85%" in html
    assert "🌧️" in html


def test_format_temperature():
    """Test Celsius passthrough, Fahrenheit conversion, and
    missing-value fallback."""
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
    """Smoke test for the 24h-strip hour card, including the weather-icon
    tooltip and the rain-chance/wind tooltips that label what the
    percentage and speed mean."""
    result = generate_hour_card_html("2024-01-01T14:00", 0, 10, 20.0, wind=15.0)
    assert "hour-card" in result
    assert "title='Clear sky'" in result
    assert "20.0°C" in result
    assert "title='Rain chance'" in result
    assert "💧 10%" in result
    assert "title='Wind'" in result
    assert "💨 15.0 km/h" in result


def test_generate_day_card_html_smoke():
    """Smoke test for the 7-day card, including the rain/wind tooltip text."""
    result = generate_day_card_html(
        "2024-01-01", 0, 10, wind=15.0, max_t=20.0, min_t=10.0
    )
    assert "day-card" in result
    assert "title='Rain chance'" in result
    assert "title='Wind'" in result


def test_generate_day_card_html_wind_converts_to_mph_under_fahrenheit():
    """Wind speed must follow the temperature unit toggle (not stay locked
    to km/h), and must always show its unit so the same bare number can't
    silently mean two different things depending on the toggle."""
    result_metric = generate_day_card_html(
        "2024-01-01", 0, 10, wind=16.0934, max_t=20.0, min_t=10.0, unit="C"
    )
    assert "💨 16.1 km/h" in result_metric

    result_imperial = generate_day_card_html(
        "2024-01-01", 0, 10, wind=16.0934, max_t=20.0, min_t=10.0, unit="F"
    )
    assert "💨 10.0 mph" in result_imperial  # 16.0934 km/h ≈ 10 mph


def test_generate_day_card_html_storm_severe_tier():
    """Thunderstorm-with-hail/severe-thunderstorm codes get the darkest tier
    class and its badge, in both languages."""
    for code in DAY_CARD_STORM_SEVERE_CODES:
        result_en = generate_day_card_html(
            "2024-01-01", code, 80, wind=15.0, max_t=20.0, min_t=10.0, lang="en"
        )
        assert "day-card-storm-severe" in result_en
        assert "day-card-storm'" not in result_en  # not misclassified as the lighter tier
        assert "storm-badge" in result_en
        assert "Severe" in result_en

        result_bg = generate_day_card_html(
            "2024-01-01", code, 80, wind=15.0, max_t=20.0, min_t=10.0, lang="bg"
        )
        assert "Опасно" in result_bg


def test_generate_day_card_html_storm_tier():
    """Heavy/violent rain, heavy snow, and plain thunderstorm codes get the
    lighter storm tier class and its badge, not the severe tier."""
    for code in DAY_CARD_STORM_CODES:
        result_en = generate_day_card_html(
            "2024-01-01", code, 80, wind=15.0, max_t=20.0, min_t=10.0, lang="en"
        )
        assert "day-card-storm'" in result_en
        assert "day-card-storm-severe" not in result_en
        assert "storm-badge" in result_en
        assert "Storm" in result_en

        result_bg = generate_day_card_html(
            "2024-01-01", code, 80, wind=15.0, max_t=20.0, min_t=10.0, lang="bg"
        )
        assert "Буря" in result_bg


def test_generate_day_card_html_no_storm_tier_for_mild_or_unknown_codes():
    """Mild weather, clear sky, and an unresolved code must not get a storm
    class or badge."""
    for code in (None, 0, 61):
        result = generate_day_card_html(
            "2024-01-01", code, 10, wind=15.0, max_t=20.0, min_t=10.0
        )
        assert "day-card-storm" not in result
        assert "storm-badge" not in result


def test_generate_forecast_row_html_smoke():
    """Smoke test for the 14-day compact row, including the
    rain/wind tooltip text."""
    result = generate_forecast_row_html(
        "2024-01-01", 0, 10, wind=15.0, max_t=20.0, min_t=10.0
    )
    assert "row-14" in result
    assert "title='Rain chance'" in result
    assert "title='Wind'" in result


def test_generate_forecast_row_html_wind_converts_to_mph_under_fahrenheit():
    """Wind speed in the 14-day row must switch to mph under the
    Fahrenheit toggle."""
    result = generate_forecast_row_html(
        "2024-01-01", 0, 10, wind=16.0934, max_t=20.0, min_t=10.0, unit="F"
    )
    assert "10.0 mph" in result  # 16.0934 km/h ≈ 10 mph


def test_generate_alert_html_error_severity():
    """Error-severity alerts get the storm icon, the severe-weather tooltip,
    and the alert-error class."""
    result = generate_alert_html("Storm incoming", "error", lang="en")
    assert "⛈️" in result
    assert "Storm incoming" in result
    assert "title='Severe Weather'" in result
    assert "alert-error" in result

    result_bg = generate_alert_html("Идва буря", "error", lang="bg")
    assert "title='Опасно време'" in result_bg


def test_generate_alert_html_warning_severity():
    """Warning-severity alerts get the caution icon, the advisory tooltip,
    and the alert-warning class."""
    result = generate_alert_html("Rain expected", "warning", lang="en")
    assert "⚠️" in result
    assert "Rain expected" in result
    assert "title='Weather Advisory'" in result
    assert "alert-warning" in result

    result_bg = generate_alert_html("Очаква се дъжд", "warning", lang="bg")
    assert "title='Предупреждение за времето'" in result_bg


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
    # Deliberately passing the wrong type to exercise safe_get's runtime
    # isinstance guard, which protects against malformed API responses
    # regardless of the declared type.
    assert safe_get([1, 2, 3], "temp", 0) is None  # pyright: ignore[reportArgumentType]


def test_safe_get_none_element():
    """Test safe_get when the element at index is None."""
    data = {"temp": [10, None, 30]}
    assert safe_get(data, "temp", 1, default=15) == 15


def test_get_time_of_day_segment_boundaries():
    """Each band boundary hour must land in the correct segment."""
    assert get_time_of_day_segment("2024-01-01T06:00") == "morning"
    assert get_time_of_day_segment("2024-01-01T11:00") == "morning"
    assert get_time_of_day_segment("2024-01-01T12:00") == "afternoon"
    assert get_time_of_day_segment("2024-01-01T17:00") == "afternoon"
    assert get_time_of_day_segment("2024-01-01T18:00") == "evening"
    assert get_time_of_day_segment("2024-01-01T21:00") == "evening"
    assert get_time_of_day_segment("2024-01-01T22:00") == "night"
    assert get_time_of_day_segment("2024-01-01T05:00") == "night"


def test_get_time_of_day_segment_invalid_input():
    """Malformed timestamps must not crash the segment lookup."""
    assert get_time_of_day_segment("") is None
    assert get_time_of_day_segment(None) is None  # pyright: ignore[reportArgumentType]


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
    """pd.to_datetime doesn't raise for '' or None, it returns NaT, whose
    strftime() raises ValueError. format_date must catch this itself
    rather than crash."""
    assert format_date("", "%A, %d %b", "en") == ""
    assert format_date(None, "%A, %d %b", "en") == "None"  # pyright: ignore[reportArgumentType]


def test_get_weather_alerts_with_missing_date():
    """A malformed/missing entry in daily['time'] must not crash alert
    generation."""
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
            {
                "name": "Sofia",
                "latitude": 42.6975,
                "longitude": 23.3241,
                "country": "Bulgaria",
            }
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
            {
                "name": "Paris",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "country": "France",
            }
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
    """A Cyrillic city name isn't matched under language=en, but is under
    language=bg; the default-language (en) search should fall back and
    still find it."""
    httpx_mock.add_response(json={"results": []})
    httpx_mock.add_response(json={
        "results": [
            {
                "name": "Ямбол",
                "latitude": 42.4833,
                "longitude": 26.5,
                "country": "Bulgaria",
            }
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
    """When the UI is already in Bulgarian, the Bulgarian-language search
    should be tried first rather than only as a fallback."""
    mock_response = {
        "results": [
            {
                "name": "Ямбол",
                "latitude": 42.4833,
                "longitude": 26.5,
                "country": "Bulgaria",
            }
        ]
    }
    httpx_mock.add_response(json=mock_response)

    result = get_coordinates("Ямбол", lang="bg")
    assert result is not None

    request = httpx_mock.get_request()
    assert request is not None
    assert "language=bg" in str(request.url)


def test_get_coordinates_not_found(httpx_mock):
    """Test behavior when a city is not found in any of the retried
    languages."""
    httpx_mock.add_response(json={"results": []}, is_reusable=True)
    result = get_coordinates("InvalidCity")
    assert result is None


def test_get_coordinates_empty_input():
    """Test that empty input returns None immediately without firing API."""
    assert get_coordinates("") is None
    assert get_coordinates("   ") is None


def test_get_coordinates_exception(httpx_mock):
    """Test that function handles timeouts and network crashes gracefully
    across retries."""
    httpx_mock.add_exception(
        httpx.TimeoutException("Timeout"), is_reusable=True
    )
    result = get_coordinates("AnyCity")
    assert result is None


# --- Weather Data Tests ---


def test_get_weather_data_full_success(httpx_mock):
    """Test successful retrieval of weather data."""
    mock_f = {
        "current": {
            "temperature_2m": 15.0,
            "wind_speed_10m": 5.0,
            "weather_code": 0,
        },
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
    """Test that the UI language is forwarded to Nominatim so results are
    localized consistently with the forward-geocoding path (which always
    requests language=en)."""
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
    """Rural coordinates can resolve to a country with no
    city/town/village/county; the known country must still be surfaced
    instead of being discarded entirely."""
    mock_response = {"address": {"country": "France"}}
    httpx_mock.add_response(json=mock_response)

    result = reverse_geocode(46.6, 2.5)
    assert result == {"name": "", "country": "France"}


def test_reverse_geocode_no_address(httpx_mock):
    """Test behavior when coordinates resolve to no address data (e.g.
    open ocean)."""
    httpx_mock.add_response(json={})
    result = reverse_geocode(0.0, 0.0)
    assert result is None


def test_reverse_geocode_exception(httpx_mock):
    """Test that function handles timeouts and network crashes gracefully."""
    httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
    result = reverse_geocode(42.6975, 23.3241)
    assert result is None


def test_build_location_from_coordinates_success(httpx_mock):
    """Test that a resolved place name and country are used when reverse
    geocoding succeeds."""
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
    """Rural coordinates with a known country but no city/town/village/county
    must show the generic place name alongside the real country, not lose the
    country entirely."""
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
