from weather_app.alerts import DAY_CARD_STORM_CODES, DAY_CARD_STORM_SEVERE_CODES
from weather_app.config import AlertSeverity
from weather_app.data.translations import TRANSLATIONS
from weather_app.formatting import format_date, format_temperature, format_wind_speed, get_wmo_info


def generate_forecast_row_html(
    date_str: str,
    code: int | None,
    rain_prob: float | int | str | None,
    wind: float | None,
    max_t: float | None,
    min_t: float | None,
    lang: str = "en",
    unit: str = "C"
) -> str:
    """Generate the HTML for a single compact 14-day forecast table row."""
    try:
        label = format_date(date_str, "%A, %d %b", lang)
    except Exception:
        label = TRANSLATIONS[lang]["unknown"]

    resolved_code = code if code is not None else -1
    desc, emoji = get_wmo_info(resolved_code, lang)
    t = TRANSLATIONS[lang]

    try:
        rain_prob_val = int(rain_prob)  # pyright: ignore[reportArgumentType]
    except (ValueError, TypeError):
        rain_prob_val = 0

    wind_str = format_wind_speed(wind, unit, lang)
    max_t_str = format_temperature(max_t, unit)
    min_t_str = format_temperature(min_t, unit)

    return (
        "<div class='row-14'>"
        f"<div class='day'>{label}</div>"
        f"<div class='emoji' title='{desc}'>{emoji}</div>"
        f"<div class='desc'>{desc}</div>"
        f"<div class='temps'>{max_t_str} <span class='min'>/ {min_t_str}</span></div>"
        f"<div class='rain' title='{t['card_rain_chance']}'>💧 {rain_prob_val}%</div>"
        f"<div class='wind' title='{t['card_wind']}'>💨 {wind_str}</div>"
        "</div>"
    )

def generate_alert_html(message: str, severity: AlertSeverity, lang: str = "en") -> str:
    """Generate the HTML for a single alert banner, matching the design's `.alert` chip.
    Severity ("warning" or "error") picks the icon, tooltip title, and the CSS
    modifier class that makes storm-level alerts read as visibly more urgent."""
    if severity == "error":
        icon = "⛈️"
        title = TRANSLATIONS[lang]["severe_weather"]
    else:
        icon = "⚠️"
        title = TRANSLATIONS[lang]["weather_advisory"]
    return (
        f"<div class='alert alert-{severity}'>"
        f"<span title='{title}'>{icon}</span><span class='text'>{message}</span>"
        "</div>"
    )

def generate_segment_risk_html(max_prob: int, has_storm: bool, is_danger: bool, lang: str = "en") -> str:
    """Generate the HTML for the rain/storm risk summary shown above the hour strip when
    a Morning/Afternoon/Evening/Night filter is active. Reuses the `.alert`/`.alert-error`
    styling so a high-risk window reads with the same urgency as a weather alert."""
    icon = "⛈️" if has_storm else ("🌧️" if is_danger else "💧")
    message = TRANSLATIONS[lang]["segment_risk_summary"].format(prob=max_prob)
    severity_class = " alert-error" if is_danger else ""
    return (
        f"<div class='alert{severity_class}'>"
        f"<span>{icon}</span><span class='text'>{message}</span>"
        "</div>"
    )

def generate_hour_card_html(
    date_str: str,
    code: int | None,
    rain_prob: float | int | str | None,
    temp: float | None,
    wind: float | None = None,
    lang: str = "en",
    unit: str = "C"
) -> str:
    """Generate the HTML for a single compact 24-hour strip card, matching the design's `.hour-card`.
    Rain chance and wind speed each get an icon plus a tooltip (matching the `.day-card` `.meta`
    pattern) so the percentage reads as "chance of rain" rather than an unlabeled number.
    Stormy codes (see DAY_CARD_STORM_CODES / DAY_CARD_STORM_SEVERE_CODES) get the same severity
    modifier class and badge treatment as the 7-day cards, so a stormy hour stands out too."""
    try:
        label = format_date(date_str, "%H:00", lang)
    except Exception:
        label = TRANSLATIONS[lang]["unknown"]

    resolved_code = code if code is not None else -1
    desc, emoji = get_wmo_info(resolved_code, lang)
    t = TRANSLATIONS[lang]

    if resolved_code in DAY_CARD_STORM_SEVERE_CODES:
        storm_class = " hour-card-storm-severe"
        storm_badge = f"<div class='storm-badge'>{t['card_storm_severe_badge']}</div>"
    elif resolved_code in DAY_CARD_STORM_CODES:
        storm_class = " hour-card-storm"
        storm_badge = f"<div class='storm-badge'>{t['card_storm_badge']}</div>"
    else:
        storm_class = ""
        storm_badge = ""

    try:
        rain_prob_val = int(rain_prob)  # pyright: ignore[reportArgumentType]
    except (ValueError, TypeError):
        rain_prob_val = 0

    temp_str = format_temperature(temp, unit)
    wind_str = format_wind_speed(wind, unit, lang)

    return (
        f"<div class='hour-card{storm_class}'>"
        f"{storm_badge}"
        f"<div class='time'>{label}</div>"
        f"<div class='emoji' title='{desc}'>{emoji}</div>"
        f"<div class='temp'>{temp_str}</div>"
        "<div class='meta'>"
        f"<span title='{t['card_rain_chance']}'>💧 {rain_prob_val}%</span>"
        f"<span title='{t['card_wind']}'>💨 {wind_str}</span>"
        "</div>"
        "</div>"
    )

def generate_day_card_html(
    date_str: str,
    code: int | None,
    rain_prob: float | int | str | None,
    wind: float | None,
    max_t: float | None,
    min_t: float | None,
    lang: str = "en",
    unit: str = "C"
) -> str:
    """Generate the HTML for a single compact 7-day card, matching the design's `.day-card`.
    Stormy codes (see DAY_CARD_STORM_CODES / DAY_CARD_STORM_SEVERE_CODES) add a severity
    modifier class and a small badge so those days stand out from the rest of the row."""
    try:
        label = format_date(date_str, "%a", lang)
    except Exception:
        label = TRANSLATIONS[lang]["unknown"]

    resolved_code = code if code is not None else -1
    desc, emoji = get_wmo_info(resolved_code, lang)
    t = TRANSLATIONS[lang]

    if resolved_code in DAY_CARD_STORM_SEVERE_CODES:
        storm_class = " day-card-storm-severe"
        storm_badge = f"<div class='storm-badge'>{t['card_storm_severe_badge']}</div>"
    elif resolved_code in DAY_CARD_STORM_CODES:
        storm_class = " day-card-storm"
        storm_badge = f"<div class='storm-badge'>{t['card_storm_badge']}</div>"
    else:
        storm_class = ""
        storm_badge = ""

    try:
        rain_prob_val = int(rain_prob)  # pyright: ignore[reportArgumentType]
    except (ValueError, TypeError):
        rain_prob_val = 0

    wind_str = format_wind_speed(wind, unit, lang)
    max_t_str = format_temperature(max_t, unit)
    min_t_str = format_temperature(min_t, unit)

    return (
        f"<div class='day-card{storm_class}'>"
        f"{storm_badge}"
        f"<div class='day'>{label}</div>"
        f"<div class='emoji' title='{desc}'>{emoji}</div>"
        f"<div class='desc'>{desc}</div>"
        f"<div class='temps'>{max_t_str} <span class='min'>/ {min_t_str}</span></div>"
        "<div class='meta'>"
        f"<span title='{t['card_rain_chance']}'>💧 {rain_prob_val}%</span>"
        f"<span title='{t['card_wind']}'>💨 {wind_str}</span>"
        "</div>"
        "</div>"
    )
