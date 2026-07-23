from typing import Any

import pandas as pd

from weather_app.data.calendar_bg import DAYS_BG, DAYS_BG_SHORT, MONTHS_BG
from weather_app.data.wmo_codes import WMO_CODES


def format_date(date_input: str, format_str: str, lang: str) -> str:
    try:
        # pandas-stubs' to_datetime overloads reference an internal Unknown-typed
        # parameter; the resolved return type here is still the correct Timestamp.
        dt = pd.to_datetime(date_input)  # pyright: ignore[reportUnknownMemberType]
    except Exception:
        return str(date_input)

    # to_datetime doesn't raise for None/"" — it returns NaT, whose strftime() raises.
    if pd.isna(dt):  # pyright: ignore[reportUnknownMemberType]
        return str(date_input)

    if lang == "bg":
        if format_str == "%A, %B %d":
            day_name = DAYS_BG.get(dt.strftime("%A"), dt.strftime("%A"))
            month_name = MONTHS_BG.get(dt.strftime("%B"), dt.strftime("%B"))
            return f"{day_name}, {month_name} {dt.strftime('%d')}"
        elif format_str == "%A, %d %b":
            day_name = DAYS_BG.get(dt.strftime("%A"), dt.strftime("%A"))
            month_name = MONTHS_BG.get(dt.strftime("%b"), dt.strftime("%b"))
            return f"{day_name}, {dt.strftime('%d')} {month_name}"
        elif format_str == "%H:00":
            return dt.strftime("%H:00")
        elif format_str == "%a":
            return DAYS_BG_SHORT.get(dt.strftime("%a"), dt.strftime("%a"))

    return dt.strftime(format_str)

def get_wmo_info(code: int, lang: str = "en") -> tuple[str, str]:
    code_data = WMO_CODES.get(code)
    if code_data and lang in code_data:
        return code_data[lang]
    if code_data and "en" in code_data:
        return code_data["en"]

    default_desc = "Unknown" if lang == "en" else "Неизвестно"
    return (default_desc, "❓")

def format_temperature(value_celsius: float | None, unit: str) -> str:
    """Format a Celsius reading for display, converting to Fahrenheit when requested."""
    if value_celsius is None:
        return f"--°{unit}"
    display_value = value_celsius * 9 / 5 + 32 if unit == "F" else value_celsius
    return f"{round(display_value, 1)}°{unit}"

def format_wind_speed(speed_kmh: float | None, unit: str, lang: str = "en") -> str:
    """Format a km/h wind reading for display, converting to mph when the
    Fahrenheit (imperial) unit is selected so wind stays consistent with temperature."""
    wind_unit = "mph" if unit == "F" else ("km/h" if lang == "en" else "км/ч")
    if speed_kmh is None:
        return f"-- {wind_unit}"
    display_value = speed_kmh * 0.621371 if unit == "F" else speed_kmh
    return f"{round(display_value, 1)} {wind_unit}"

def get_wind_speed_class(speed_kmh: float | None) -> str:
    """Classify a raw km/h wind reading into a CSS severity tier so the displayed value
    can be color-coded. Always classifies off the underlying km/h figure, independent
    of the km/h-to-mph conversion format_wind_speed applies for display."""
    if speed_kmh is None or speed_kmh < 20:
        return ""
    if speed_kmh < 40:
        return "wind-breezy"
    if speed_kmh < 70:
        return "wind-strong"
    return "wind-severe"

def get_time_of_day_segment(time_str: str) -> str | None:
    """Classify an ISO hourly timestamp into a morning/afternoon/evening/night band."""
    try:
        hour = pd.to_datetime(time_str).hour  # pyright: ignore[reportUnknownMemberType]
    except Exception:
        return None
    if pd.isna(hour):  # pyright: ignore[reportUnknownMemberType]
        return None
    if 6 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 22:
        return "evening"
    return "night"

def get_default_hour_time_filter(current_time: str | None) -> str:
    """Pick the hour-of-day pill to preselect, defaulting to the current time's segment."""
    if not current_time:
        return "all"
    return get_time_of_day_segment(current_time) or "all"

def safe_get(data_dict: dict[str, Any] | None, key: str, idx: int, default: Any = None) -> Any:
    """Safely fetch index from dictionary arrays to prevent IndexErrors on missing API data."""
    if not isinstance(data_dict, dict):
        return default
    arr: Any = data_dict.get(key, [])
    # isinstance narrowing against a bare "list" (no element type available here)
    # resolves to list[Unknown] rather than list[Any]; the values are genuinely
    # untyped JSON data, so this is a stub-precision limit, not a real bug.
    if isinstance(arr, list) and idx < len(arr) and arr[idx] is not None:  # pyright: ignore[reportUnknownArgumentType]
        return arr[idx]  # pyright: ignore[reportUnknownVariableType]
    return default
