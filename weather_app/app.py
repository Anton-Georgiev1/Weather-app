import html
from typing import Any

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit_geolocation import streamlit_geolocation  # pyright: ignore[reportMissingTypeStubs]
from streamlit_local_storage import LocalStorage  # pyright: ignore[reportMissingTypeStubs]

from weather_app.alerts import NEAR_TERM_LOOKAHEAD_HOURS, get_near_term_alerts, get_weather_alerts, near_term_storm_is_today, summarize_segment_risk
from weather_app.config import SKYWATCH_URL
from weather_app.data.seasons import SEASON_THEMES
from weather_app.data.translations import TRANSLATIONS
from weather_app.formatting import format_date, format_temperature, format_wind_speed, get_time_of_day_segment, get_wmo_info, safe_get
from weather_app.render import generate_alert_html, generate_day_card_html, generate_forecast_row_html, generate_hour_card_html, generate_segment_risk_html
from weather_app.storage import load_last_language, load_last_location, save_last_language, save_last_location
from weather_app.theme import get_theme_css
from weather_app.weather_api import build_location_from_coordinates, get_coordinates, get_weather_data


def main():
    if "season" not in st.session_state:
        st.session_state.season = "summer"
    if "unit" not in st.session_state:
        st.session_state.unit = "C"
    if "auto_refresh_enabled" not in st.session_state:
        # Off by default: the whole dashboard (including the Radar/SkyWatch iframe
        # embeds) lives in one fragment, so an enabled timer silently reloads those
        # embeds every 15 minutes even with no user interaction. Opt-in avoids that
        # surprise for anyone who never touches the toggle.
        st.session_state.auto_refresh_enabled = False

    current_season = st.session_state.season
    current_unit = st.session_state.unit

    # set_page_config must be the very first Streamlit command, so it can't wait on the
    # local storage read below (which needs a mounted component). Fall back to whatever
    # language guess is already in session state; the local storage read just after fixes
    # session_state.lang itself before any visible content renders, so on a fresh session
    # the only thing that can lag by a run is this literal browser-tab title.
    page_title_lang = st.session_state.get("lang", "en")
    page_title = "Weather App" if page_title_lang == "en" else "Приложение за времето"
    st.set_page_config(page_title=page_title, page_icon="🌤️", layout="wide")

    theme = SEASON_THEMES[current_season]
    st.markdown(get_theme_css(theme), unsafe_allow_html=True)

    local_storage = LocalStorage()
    if "lang" not in st.session_state:
        saved_lang = load_last_language(local_storage)
        st.session_state.lang = saved_lang if saved_lang in TRANSLATIONS else "en"

    # The language switch below calls st.rerun() immediately so the whole page redraws in
    # the new language in one go. Writing to local storage in that same instant would tear
    # the write's component down before the browser applies it, so the write is deferred to
    # this next, rerun-free run instead.
    pending_lang_save = st.session_state.pop("pending_lang_save", None)
    if pending_lang_save:
        save_last_language(local_storage, pending_lang_save)

    current_lang = st.session_state.lang
    t = TRANSLATIONS[current_lang]

    # --- Main Page Header Layout: brand + season swatches + auto-refresh + EN/BG + degC/degF ---
    with st.container(key="app_header"):
        col_brand, col_controls = st.columns([2, 4])

        with col_brand:
            brand_html = (
                "<div class='brand-row'>"
                f"<div class='brand-icon' title='{theme[f'label_{current_lang}']}'>{theme['emoji']}</div>"
                "<div>"
                f"<div class='brand-title'>{t['brand_title']}</div>"
                f"<div class='brand-sub'>{t['brand_sub']}</div>"
                "</div>"
                "</div>"
            )
            st.markdown(brand_html, unsafe_allow_html=True)

        with col_controls, st.container(key="header_controls"):
            col_season, col_refresh, col_lang, col_unit = st.columns(4)

            with col_season:
                season_keys = list(SEASON_THEMES.keys())
                season_legend = t["season_label"] + ": " + " · ".join(
                    f"{SEASON_THEMES[key]['emoji']} {SEASON_THEMES[key][f'label_{current_lang}']}"
                    for key in season_keys
                )
                selected_season = st.segmented_control(
                    label=t["season_label"],
                    options=season_keys,
                    format_func=lambda key: SEASON_THEMES[key]["emoji"],
                    default=current_season,
                    required=True,
                    key="season_selector",
                    label_visibility="collapsed",
                    help=season_legend
                )

            with col_refresh, st.container(key="refresh_group"):
                col_refresh_toggle, col_refresh_button = st.columns(2)
                with col_refresh_toggle:
                    st.session_state.auto_refresh_enabled = st.toggle(
                        t["auto_refresh_label"],
                        value=st.session_state.auto_refresh_enabled,
                        help=t["auto_refresh_help"]
                    )
                with col_refresh_button:
                    # Populated later by the render_weather_dashboard fragment so the
                    # refresh button lives in the header but its click still only
                    # reruns the fragment, not the whole page.
                    refresh_button_slot = st.container()

            with col_lang:
                lang_options = {"EN": "en", "BG": "bg"}
                current_lang_label = "EN" if current_lang == "en" else "BG"
                selected_lang_label = st.segmented_control(
                    label=t["lang_label"],
                    options=list(lang_options.keys()),
                    default=current_lang_label,
                    required=True,
                    key="main_language_selector",
                    label_visibility="collapsed"
                )
                selected_lang = lang_options.get(selected_lang_label, current_lang)

            with col_unit:
                unit_options = {"°C": "C", "°F": "F"}
                current_unit_label = "°C" if current_unit == "C" else "°F"
                selected_unit_label = st.segmented_control(
                    label="Unit",
                    options=list(unit_options.keys()),
                    default=current_unit_label,
                    required=True,
                    key="unit_selector",
                    label_visibility="collapsed"
                )
                selected_unit = unit_options.get(selected_unit_label, current_unit)

    # If any control changed, persist it and rerun so the whole page reflects the new state
    if selected_season != current_season:
        st.session_state.season = selected_season
        st.rerun()
    if selected_lang != current_lang:
        st.session_state.lang = selected_lang
        st.session_state.pending_lang_save = selected_lang
        st.rerun()
    if selected_unit != current_unit:
        st.session_state.unit = selected_unit
        st.rerun()

    lang = st.session_state.lang
    unit = st.session_state.unit
    t = TRANSLATIONS[lang]

    # Initialize session states for specific day drill-down AND remembering user inputs
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None
    if "saved_city" not in st.session_state or "saved_country" not in st.session_state:
        last_location = load_last_location(local_storage)
        st.session_state.saved_city = last_location["city"]
        st.session_state.saved_country = last_location["country"]
    if "location_source" not in st.session_state:
        st.session_state.location_source = "manual"
    if "geo_location" not in st.session_state:
        st.session_state.geo_location = None
    if "geo_processed_coords" not in st.session_state:
        st.session_state.geo_processed_coords = None

    # Input Layout
    with st.container(key="location_card"):
        with st.container(key="search_top"):
            col_geo_icon, col_geo_hint, col_geo_divider = st.columns([1, 3, 5])
            with col_geo_icon:
                geo_result = streamlit_geolocation()
            with col_geo_hint:
                st.caption(t["geo_section_label"])
            with col_geo_divider:
                st.markdown(
                    '<div class="location-divider">'
                    '<span class="location-divider-line"></span>'
                    f'<span class="location-divider-text">{t["geo_divider_text"]}</span>'
                    '<span class="location-divider-line"></span>'
                    '</div>',
                    unsafe_allow_html=True
                )

            geo_lat = geo_result.get("latitude") if geo_result else None
            geo_lon = geo_result.get("longitude") if geo_result else None

            if geo_lat is not None and geo_lon is not None:
                current_coords = (geo_lat, geo_lon)
                # The component keeps returning the same last-known reading on every rerun
                # (it only sends a new value once the user clicks it again), so a plain
                # coordinate comparison is what tells a fresh click apart from that replay.
                is_new_geo_request = current_coords != st.session_state.geo_processed_coords
                if is_new_geo_request:
                    st.session_state.geo_processed_coords = current_coords
                    resolved_location = build_location_from_coordinates(geo_lat, geo_lon, lang)
                    st.session_state.geo_location = resolved_location
                    st.session_state.location_source = "geo"
                    st.session_state.selected_date = None
                    if resolved_location["country"]:
                        st.session_state.saved_city = resolved_location["name"]
                        st.session_state.saved_country = resolved_location["country"]
                        save_last_location(local_storage, resolved_location["name"], resolved_location["country"])
                        st.toast(t["geo_success_toast"].format(
                            city=resolved_location["name"], country=resolved_location["country"]
                        ))
                    else:
                        st.session_state.saved_city = ""
                        st.session_state.saved_country = ""
                    st.rerun()

        c_in1, c_in2, c_in3 = st.columns([1, 1, 1])

        with c_in1:
            city_input = st.text_input(
                t["city_label"],
                value=st.session_state.saved_city,
                placeholder=t["city_placeholder"]
            )
        with c_in2:
            country_input = st.text_input(
                t["country_label"],
                value=st.session_state.saved_country,
                placeholder=t["country_placeholder"]
            )
        with c_in3:
            with st.container(key="search_action"):
                # Streamlit already reruns (and refetches with the current inputs) on any
                # widget interaction, so this button is a visual affordance matching the
                # design rather than a gate the fetch logic below depends on.
                st.button(t["search_button"], type="primary", use_container_width=True, key="search_button")

    # Automatically update our memory state with whatever is currently in the boxes
    # NOTE: geo_processed_coords is intentionally left untouched here. The geolocation
    # component keeps returning the same last-known reading on every rerun (it only
    # sends a new value once the user clicks it again), so clearing this guard would
    # make the app treat that stale reading as "new" on the next rerun and silently
    # snap back to the geolocated city/country, discarding the manual edit.
    if city_input != st.session_state.saved_city:
        st.session_state.saved_city = city_input
        st.session_state.selected_date = None  # Clear selected day when user searches for a new city
        st.session_state.location_source = "manual"
        st.session_state.geo_location = None
        save_last_location(local_storage, st.session_state.saved_city, st.session_state.saved_country)

    if country_input != st.session_state.saved_country:
        st.session_state.saved_country = country_input
        st.session_state.location_source = "manual"
        st.session_state.geo_location = None
        save_last_location(local_storage, st.session_state.saved_city, st.session_state.saved_country)

    # Main Weather Fetching Section
    using_geo_location = (
        st.session_state.location_source == "geo" and st.session_state.geo_location is not None
    )

    # The generic fallback name is language-dependent; keep it in sync with the current UI language.
    active_geo_location = st.session_state.geo_location
    if using_geo_location and active_geo_location is not None and not active_geo_location.get("country"):
        active_geo_location["name"] = t["geo_header_generic"]

    refresh_interval = "15m" if st.session_state.auto_refresh_enabled else None

    @st.fragment(run_every=refresh_interval)
    def render_weather_dashboard(
        location: dict[str, Any],
        lang: str,
        unit: str,
        using_geo_location: bool,
        refresh_button_slot: DeltaGenerator
    ) -> None:
        """Fetch and display current/hourly/daily weather for a resolved location.
        Wrapped in a fragment so the refresh button (rendered into a slot back in
        the header) and the auto-refresh timer only re-run this section, not the
        whole page (search inputs, tabs, scroll, etc.)."""
        t = TRANSLATIONS[lang]

        with refresh_button_slot:
            st.button(t["refresh_now_button"], key="refresh_now_button")

        lat, lon = location["latitude"], location["longitude"]
        with st.spinner(t["fetching"]):
            f_data = get_weather_data(lat, lon)

        if f_data:
            hourly = f_data.get("hourly", {})
            daily = f_data.get("daily", {})
            curr = f_data.get("current", {})

            # Hourly data starts at 00:00 of the current day, so index 0 is
            # usually already in the past by the time the user looks at it.
            # Find the first hour that hasn't happened yet -- this anchors both
            # the near-term rain/storm alert check and the 24h strip below.
            current_time: str | None = curr.get("time")
            # Shown in the location's own local time (Open-Meteo's timezone=auto
            # response), not the server's clock -- those can differ by hours
            # depending on which timezone the app happens to be hosted in.
            if current_time:
                st.caption(t["last_updated"].format(time=format_date(current_time, "%H:%M", lang)))
            current_hour_key = f"{current_time[:13]}:00" if current_time else None
            upcoming_start_idx = 0
            if current_hour_key and hourly and "time" in hourly:
                for idx, time_str in enumerate(hourly["time"]):
                    if time_str >= current_hour_key:
                        upcoming_start_idx = idx
                        break

            # --- Main Screen Location + Hero ---
            # Escaped because this is third-party geocoding/reverse-geocoding data
            # (Open-Meteo / OpenStreetMap Nominatim) rendered via unsafe_allow_html.
            location_label = html.escape(location["name"])
            if location.get("country"):
                location_label += f", {html.escape(location['country'])}"
            st.markdown(
                f"<div class='location'><span title='{t['geo_header_generic']}'>📍</span><span class='name'>{location_label}</span></div>",
                unsafe_allow_html=True
            )

            if using_geo_location and not location.get("country"):
                st.info(t["geo_reverse_lookup_failed"])

            current_code = curr.get("weather_code")
            current_desc, current_emoji = get_wmo_info(
                current_code if current_code is not None else -1, lang
            )
            wind_speed_val = curr.get("wind_speed_10m")
            wind_str = format_wind_speed(wind_speed_val, unit, lang)
            humidity_val = curr.get("relative_humidity_2m")
            humidity_str = f"{humidity_val}%" if humidity_val is not None else "--%"
            rain_chance_val = safe_get(daily, "precipitation_probability_max", 0)
            rain_chance_str = f"{rain_chance_val}%" if rain_chance_val is not None else "--%"

            # Current hour plus the same near-term window used for the near-term
            # rain/storm alert above, so the two stay consistent with each other.
            near_rain_probs = [
                prob for idx in range(upcoming_start_idx, upcoming_start_idx + NEAR_TERM_LOOKAHEAD_HOURS + 1)
                if (prob := safe_get(hourly, "precipitation_probability", idx)) is not None
            ]
            near_rain_chance_val = max(near_rain_probs) if near_rain_probs else None
            near_rain_chance_str = f"{near_rain_chance_val}%" if near_rain_chance_val is not None else "--%"

            hero_html = (
                "<div class='hero'>"
                "<div class='hero-main'>"
                f"<div class='hero-emoji' title='{current_desc}'>{current_emoji}</div>"
                "<div>"
                f"<div class='hero-temp'>{format_temperature(curr.get('temperature_2m'), unit)}</div>"
                f"<div class='hero-feels'>{t['card_feels_like']} {format_temperature(curr.get('apparent_temperature'), unit)}</div>"
                f"<div class='hero-desc'>{current_desc}</div>"
                "</div>"
                "</div>"
                "<div class='stat-grid'>"
                f"<div class='stat-chip'><div class='label'>{t['card_day_max']}</div><div class='value'>{format_temperature(safe_get(daily, 'temperature_2m_max', 0), unit)}</div></div>"
                f"<div class='stat-chip'><div class='label'>{t['card_day_min']}</div><div class='value'>{format_temperature(safe_get(daily, 'temperature_2m_min', 0), unit)}</div></div>"
                f"<div class='stat-chip'><div class='label'>{t['card_wind']}</div><div class='value'>{wind_str}</div></div>"
                f"<div class='stat-chip'><div class='label'>{t['card_hum']}</div><div class='value'>{humidity_str}</div></div>"
                f"<div class='stat-chip'><div class='label'>{t['card_rain_chance']}</div><div class='value'>{rain_chance_str}</div></div>"
                f"<div class='stat-chip' title='{t['card_rain_chance_soon_help']}'><div class='label'>{t['card_rain_chance_soon']}</div><div class='value'>{near_rain_chance_str}</div></div>"
                "</div>"
                "</div>"
            )
            st.markdown(hero_html, unsafe_allow_html=True)

            # --- Alerts Section (only shown when there's an actual alert) ---
            # Near-term (this hour / next hour) alerts come first since they're
            # the most time-critical, ahead of the multi-day lookahead alerts.
            near_term_alerts = get_near_term_alerts(hourly, upcoming_start_idx, lang=lang) if hourly and "time" in hourly else []
            # A near-term storm already describes today's severe weather -- don't repeat
            # it via the daily lookahead's own "today" entry (see get_weather_alerts' docstring).
            daily_alerts = (
                get_weather_alerts(
                    daily, lang=lang, unit=unit,
                    skip_today_precip=near_term_storm_is_today(near_term_alerts, daily),
                    hourly_data=hourly, upcoming_start_idx=upcoming_start_idx
                )
                if daily and "time" in daily else []
            )
            alerts = near_term_alerts + daily_alerts
            if alerts:
                st.divider()
                st.subheader(t["alerts_header"].format(city=location['name']))
                alerts_html = "".join(
                    generate_alert_html(alert["message"], alert["severity"], lang=lang) for alert in alerts
                )
                st.markdown(alerts_html, unsafe_allow_html=True)

            st.divider()

            # --- Immediate 24h Hourly Track (horizontal scroll strip) ---
            if hourly and "time" in hourly:
                st.subheader(t["next_24h"])

                if "show_past_hours" not in st.session_state:
                    st.session_state.show_past_hours = False
                st.session_state.show_past_hours = st.toggle(
                    t["show_past_hours"], value=st.session_state.show_past_hours
                )

                start_idx = 0 if st.session_state.show_past_hours else upcoming_start_idx
                end_idx = min(start_idx + 24, len(hourly["time"]))
                hour_indices = list(range(start_idx, end_idx))

                time_filter_keys = ["all", "morning", "afternoon", "evening", "night"]
                time_filter_labels = {
                    "all": t["time_filter_all"],
                    "morning": t["time_filter_morning"],
                    "afternoon": t["time_filter_afternoon"],
                    "evening": t["time_filter_evening"],
                    "night": t["time_filter_night"],
                }
                if "hour_time_filter" not in st.session_state:
                    st.session_state.hour_time_filter = "all"
                st.session_state.hour_time_filter = st.pills(
                    t["time_filter_label"],
                    options=time_filter_keys,
                    format_func=lambda key: time_filter_labels[key],
                    default=st.session_state.hour_time_filter,
                    required=True,
                    label_visibility="collapsed",
                    key="hour_time_filter_pills",
                )

                if st.session_state.hour_time_filter != "all":
                    hour_indices = [
                        idx for idx in hour_indices
                        if get_time_of_day_segment(hourly["time"][idx]) == st.session_state.hour_time_filter
                    ]

                    if hour_indices:
                        segment_risk = summarize_segment_risk(hourly, hour_indices)
                        st.markdown(
                            generate_segment_risk_html(
                                segment_risk["max_prob"],
                                segment_risk["has_storm"],
                                segment_risk["is_danger"],
                                lang=lang
                            ),
                            unsafe_allow_html=True
                        )

                if hour_indices:
                    hour_cards_html = "".join(
                        generate_hour_card_html(
                            hourly["time"][idx],
                            code=safe_get(hourly, "weather_code", idx),
                            rain_prob=safe_get(hourly, "precipitation_probability", idx),
                            temp=safe_get(hourly, "temperature_2m", idx),
                            wind=safe_get(hourly, "wind_speed_10m", idx),
                            lang=lang,
                            unit=unit
                        )
                        for idx in hour_indices
                    )
                    st.markdown(f"<div class='hour-strip'>{hour_cards_html}</div>", unsafe_allow_html=True)
                else:
                    st.info(t["no_hours_in_segment"])
            else:
                st.warning(t["hourly_unavailable"])

            st.divider()

            # --- Helper function to display card + button (7-day tab) ---
            def display_daily_column(st_col: DeltaGenerator, data_index: int, tab_prefix: str) -> None:
                with st_col:
                    st.markdown(
                        generate_day_card_html(
                            daily["time"][data_index],
                            code=safe_get(daily, "weather_code", data_index),
                            rain_prob=safe_get(daily, "precipitation_probability_max", data_index),
                            wind=safe_get(daily, "wind_speed_10m_max", data_index),
                            max_t=safe_get(daily, "temperature_2m_max", data_index),
                            min_t=safe_get(daily, "temperature_2m_min", data_index),
                            lang=lang,
                            unit=unit
                        ),
                        unsafe_allow_html=True
                    )
                    # UNIQUE KEY: combining the tab name and the date to prevent duplicate key crashes
                    btn_key = f"btn_{tab_prefix}_{daily['time'][data_index]}"
                    if st.button(t["btn_24h"], key=btn_key, use_container_width=True):
                        st.session_state.selected_date = daily["time"][data_index]
                        st.rerun(scope="fragment")

            # --- Long Term Forecasts & Radar Tabs ---
            if daily and "time" in daily:
                tab7, tab14, tab_radar, tab_skywatch = st.tabs(
                    [t["forecast_7day"], t["forecast_14day"], t["live_radar"], t["skywatch_tab"]]
                )

                with tab7:
                    with st.container(key="forecast_tab7"):
                        num_7 = min(7, len(daily["time"]))
                        cols = st.columns(7)
                        for i in range(num_7):
                            display_daily_column(cols[i], i, "tab7")

                with tab14:
                    with st.container(key="forecast_tab14"):
                        num_14 = min(14, len(daily["time"]))
                        for idx in range(num_14):
                            row_col, btn_col = st.columns([6, 1])
                            with row_col:
                                st.markdown(
                                    generate_forecast_row_html(
                                        daily["time"][idx],
                                        code=safe_get(daily, "weather_code", idx),
                                        rain_prob=safe_get(daily, "precipitation_probability_max", idx),
                                        wind=safe_get(daily, "wind_speed_10m_max", idx),
                                        max_t=safe_get(daily, "temperature_2m_max", idx),
                                        min_t=safe_get(daily, "temperature_2m_min", idx),
                                        lang=lang,
                                        unit=unit
                                    ),
                                    unsafe_allow_html=True
                                )
                            with btn_col:
                                btn_key = f"btn_tab14_{daily['time'][idx]}"
                                if st.button(t["btn_24h"], key=btn_key, use_container_width=True):
                                    st.session_state.selected_date = daily["time"][idx]
                                    st.rerun(scope="fragment")

                with tab_radar:
                    st.markdown("<br>", unsafe_allow_html=True)

                    # --- BIG REDIRECT BUTTON TO WINDY.COM ---
                    windy_redirect_url = f"https://www.windy.com/-Weather-radar-radar?radar,{lat},{lon},6"
                    st.link_button(t["open_windy"], url=windy_redirect_url, type="primary")

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Keeps the embedded preview view visible just underneath
                    st.markdown(
                        "<div class='radar-frame'>"
                        f"<iframe src='https://embed.windy.com/embed2.html?lat={lat}&lon={lon}&zoom=6&level=surface&overlay=radar&product=radar&menu=&message=true&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1&play=1' frameborder='0'></iframe>"
                        "</div>",
                        unsafe_allow_html=True
                    )

                with tab_skywatch:
                    st.markdown("<br>", unsafe_allow_html=True)

                    # --- BIG REDIRECT BUTTON TO SKYWATCH BG ---
                    st.link_button(t["open_skywatch"], url=SKYWATCH_URL, type="primary")

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Keeps the embedded preview view visible just underneath
                    st.markdown(
                        "<div class='radar-frame'>"
                        f"<iframe src='{SKYWATCH_URL}' frameborder='0'></iframe>"
                        "</div>",
                        unsafe_allow_html=True
                    )

                # --- Specific Day Clicked Section ---
                if st.session_state.selected_date:
                    st.divider()
                    sel_date = st.session_state.selected_date
                    formatted_sel_date = format_date(sel_date, "%A, %B %d", lang)

                    st.subheader(t["hourly_header"].format(formatted_date=formatted_sel_date))

                    # Find all hour indices that match the clicked date
                    day_indices = [idx for idx, time_str in enumerate(hourly.get("time", [])) if time_str.startswith(sel_date)]

                    if day_indices:
                        day_cards_html = "".join(
                            generate_hour_card_html(
                                hourly["time"][idx],
                                code=safe_get(hourly, "weather_code", idx),
                                rain_prob=safe_get(hourly, "precipitation_probability", idx),
                                temp=safe_get(hourly, "temperature_2m", idx),
                                wind=safe_get(hourly, "wind_speed_10m", idx),
                                lang=lang,
                                unit=unit
                            )
                            for idx in day_indices
                        )
                        st.markdown(f"<div class='hour-strip'>{day_cards_html}</div>", unsafe_allow_html=True)
                    else:
                        st.info(t["hourly_far_future"])

            else:
                st.warning(t["daily_unavailable"])
        else:
            st.error(t["fetch_failed"])

    if using_geo_location or city_input:
        with st.spinner(t["fetching"]):
            location = (
                st.session_state.geo_location if using_geo_location
                else get_coordinates(city_input, country_input, lang=lang)
            )

        if location:
            render_weather_dashboard(location, lang, unit, using_geo_location, refresh_button_slot)
        else:
            st.warning(t["loc_not_found"])
