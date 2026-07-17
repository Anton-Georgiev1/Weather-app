from typing import Any

from weather_app.config import AlertSeverity
from weather_app.data.translations import TRANSLATIONS
from weather_app.formatting import format_date, format_wind_speed, get_wmo_info, safe_get

ALERT_LOOKAHEAD_DAYS = 3

# Near-term (this hour / next hour) rain-vs-storm alert tuning. Open-Meteo's
# hourly array is our finest resolution (no minutely data is fetched), so
# "next 30 min" isn't representable -- this checks the current and next
# hourly slot instead.
NEAR_TERM_LOOKAHEAD_HOURS = 1
NEAR_TERM_RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 66, 80, 81}
# Same severe-weather codes as the daily alert's precip check (65, 67, 75, 82, 86, 95, 96, 99):
# thunderstorms, violent/heavy rain, and heavy snow all warrant the storm-tier alert.
NEAR_TERM_STORM_CODES = {65, 67, 75, 82, 86, 95, 96, 99}
NEAR_TERM_RAIN_PROBABILITY_THRESHOLD = 70

# 7-day forecast card severity tiers, so a stormy day's card stands out from the rest
# of the row. Thunderstorm-with-hail/severe-thunderstorm get the darker "severe" tier;
# the rest of NEAR_TERM_STORM_CODES gets the lighter "storm" tier. This split is only
# for the card's own two-tier display and is intentionally independent of the near-term
# alert's severity (which treats all of NEAR_TERM_STORM_CODES, including plain
# thunderstorm/95, as top severity) -- the two lists aren't meant to move in lockstep.
DAY_CARD_STORM_SEVERE_CODES = {96, 99}
DAY_CARD_STORM_CODES = NEAR_TERM_STORM_CODES - DAY_CARD_STORM_SEVERE_CODES

def get_weather_alerts(
    daily_data: dict[str, Any],
    lang: str = "en",
    unit: str = "C",
    skip_today_precip: bool = False
) -> list[dict[str, Any]]:
    """Analyze daily data for severe weather or wind alerts, limited to the near term
    (ALERT_LOOKAHEAD_DAYS) since forecasts this far out are unreliable for alerting.

    skip_today_precip drops today's severe-weather-condition alert (not the wind one):
    the daily forecast has a single weather_code per day, so when the near-term (this
    hour/next hour) check has already raised a storm alert, today's entry here would
    describe that same storm a second time."""
    alerts: list[dict[str, Any]] = []
    if not daily_data or "time" not in daily_data:
        return alerts

    for i in range(min(len(daily_data["time"]), ALERT_LOOKAHEAD_DAYS)):
        wcode = safe_get(daily_data, "weather_code", i)
        prob = safe_get(daily_data, "precipitation_probability_max", i, 0)
        wind = safe_get(daily_data, "wind_speed_10m_max", i, 0)
        day_name = format_date(daily_data["time"][i], "%A, %B %d", lang)

        if wcode in [65, 67, 75, 82, 86, 95, 96, 99] and not (i == 0 and skip_today_precip):
            condition_name = get_wmo_info(wcode, lang)[0]
            msg_tpl = TRANSLATIONS[lang]["alert_precip"]
            alerts.append({
                "severity": "error",
                "message": msg_tpl.format(day_name=day_name, condition_name=condition_name, prob=prob)
            })

        if wind is not None and wind > 50:
            msg_tpl = TRANSLATIONS[lang]["alert_wind"]
            alerts.append({
                "severity": "warning",
                "message": msg_tpl.format(day_name=day_name, wind=format_wind_speed(wind, unit, lang))
            })
    return alerts

def get_near_term_alerts(hourly_data: dict[str, Any], upcoming_start_idx: int, lang: str = "en") -> list[dict[str, Any]]:
    """Check the current and next hourly forecast slot for rain or storm conditions,
    escalating to the storm severity when the worse of the two hours is a thunderstorm
    or heavy/violent precipitation code."""
    if not hourly_data or "time" not in hourly_data:
        return []

    severity_rank: dict[AlertSeverity, int] = {"warning": 1, "error": 2}
    best_rank = 0
    best_severity: AlertSeverity | None = None
    best_code: int | None = None
    best_prob: float | int = 0
    best_idx: int | None = None

    for idx in range(upcoming_start_idx, upcoming_start_idx + NEAR_TERM_LOOKAHEAD_HOURS + 1):
        wcode = safe_get(hourly_data, "weather_code", idx)
        prob = safe_get(hourly_data, "precipitation_probability", idx, 0)

        severity: AlertSeverity
        if wcode in NEAR_TERM_STORM_CODES:
            severity = "error"
        elif wcode in NEAR_TERM_RAIN_CODES or prob >= NEAR_TERM_RAIN_PROBABILITY_THRESHOLD:
            severity = "warning"
        else:
            continue

        # Keep the higher-severity hour; on a tie, keep the sooner one
        # (first match wins) since idx increases with the loop.
        if severity_rank[severity] <= best_rank:
            continue
        best_rank, best_severity, best_code, best_prob, best_idx = severity_rank[severity], severity, wcode, prob, idx

    if best_severity is None:
        return []

    # A probability-only trigger (prob >= threshold but wcode isn't itself a
    # rain/storm code) shouldn't borrow wcode's condition text -- e.g. a "Clear
    # sky" wcode with an 85% precipitation_probability would otherwise render
    # as "Clear sky expected... (85% chance of precipitation)", contradicting
    # itself. Only trust wcode's description when it's actually why we alerted.
    if best_code is not None and (best_code in NEAR_TERM_RAIN_CODES or best_code in NEAR_TERM_STORM_CODES):
        condition_name = get_wmo_info(best_code, lang)[0]
    else:
        condition_name = TRANSLATIONS[lang]["condition_rain_generic"]
    msg_key = "alert_storm_soon" if best_severity == "error" else "alert_rain_soon"
    msg_tpl = TRANSLATIONS[lang][msg_key]
    # date lets callers tell whether this alert's triggering hour actually falls
    # on "today" (the lookahead window can cross into tomorrow's first hour).
    best_date = hourly_data["time"][best_idx][:10] if best_idx is not None else None
    return [{
        "severity": best_severity,
        "message": msg_tpl.format(condition_name=condition_name, prob=best_prob),
        "date": best_date
    }]

def near_term_storm_is_today(near_term_alerts: list[dict[str, Any]], daily_data: dict[str, Any] | None) -> bool:
    """True when a near-term (this/next hour) storm alert's triggering hour actually
    falls on today's calendar date. The near-term lookahead can cross into tomorrow's
    first hour (e.g. checked at 23:00), so this can't just be "any near-term error
    alert" -- get_weather_alerts' skip_today_precip would otherwise wrongly drop a
    distinct, earlier storm that's genuinely today's own alert."""
    if not daily_data or not daily_data.get("time"):
        return False
    today_date = daily_data["time"][0]
    return any(
        alert["severity"] == "error" and alert.get("date") == today_date
        for alert in near_term_alerts
    )
