def get_theme_css(theme: dict[str, str]) -> str:
    """Build the seasonal <link>+<style> block: CSS custom properties from the
    season's palette (see SEASON_THEMES), plus the fixed component styling that
    references them so switching seasons re-skins the whole app."""
    return f"""
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root {{
    --page-bg: {theme['page_bg']};
    --surface: {theme['surface']};
    --border: {theme['border']};
    --text: {theme['text']};
    --accent: {theme['accent']};
    --accent-deep: {theme['accent_deep']};
    --accent-soft: {theme['accent_soft']};
    --accent-grad: {theme['accent_grad']};
    --hero-grad: {theme['hero_grad']};
    --accent-shadow: {theme['accent_shadow']};
    --card-shadow: {theme['card_shadow']};
    --alert-error-bg: color-mix(in srgb, var(--accent-soft) 78%, #c62828 22%);
    --alert-error-border: color-mix(in srgb, var(--accent-deep) 40%, #c62828 60%);
    --alert-error-text: color-mix(in srgb, var(--accent-deep) 55%, #3a0a0a 45%);
    --alert-error-shadow: color-mix(in srgb, var(--accent-shadow) 55%, rgba(198,40,40,.45) 45%);
    --alert-error-shadow-strong: color-mix(in srgb, var(--accent-shadow) 40%, rgba(198,40,40,.6) 60%);
    --storm-bg: color-mix(in srgb, var(--accent-deep) 42%, var(--surface) 58%);
    --storm-border: var(--accent-deep);
    --storm-shadow: var(--accent-shadow);
    --storm-shadow-hover: 0 6px 18px var(--accent-shadow);
    /* Slightly darker than --storm-border so white badge text clears WCAG AA (4.5:1)
       even on the lightest accent-deep tone (summer's #b06c22, ~4.2:1 unmixed). */
    --storm-badge-bg: color-mix(in srgb, var(--accent-deep) 85%, black 15%);
    --storm-severe-bg: color-mix(in srgb, var(--accent-deep) 68%, black 32%);
    --storm-severe-border: color-mix(in srgb, var(--accent-deep) 50%, black 50%);
    --storm-severe-shadow: color-mix(in srgb, var(--accent-shadow) 70%, black 30%);
    --storm-severe-shadow-hover: 0 10px 26px color-mix(in srgb, var(--accent-shadow) 70%, black 30%);
    --wind-breezy: color-mix(in srgb, var(--text) 35%, #d9a017 65%);
    --wind-strong: color-mix(in srgb, var(--text) 20%, #e8710a 80%);
    --wind-severe: color-mix(in srgb, var(--text) 10%, #c62828 90%);
}}

html, [data-testid="stAppViewContainer"], .stApp {{
    background: var(--page-bg) !important;
    font-family: 'Inter', system-ui, sans-serif;
}}
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {{
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    color: var(--text);
}}
/* Hides the top deploy bar completely */
[data-testid="stHeader"] {{ visibility: hidden; display: none; }}

/* Reduce the default top padding Streamlit applies to the main block-container
   now that the deploy bar/header above it is hidden. */
[data-testid="stAppViewContainer"] .block-container {{
    padding: 1rem 1rem 10rem;
}}

/* ---------- BUTTONS ---------- */
.stButton button[kind="primary"],
[data-testid="stLinkButton"] a[kind="primary"] {{
    background: var(--accent-grad) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    border-radius: .625rem !important;
    box-shadow: 0 3px 10px var(--accent-shadow) !important;
}}
.stButton button[kind="secondary"] {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: .625rem !important;
    font-weight: 700 !important;
}}

/* Refresh button loading state (the "refresh_now_button_loading" key that
   briefly replaces the normal button while its fetch is in flight): a filling
   bar sweeps behind the label, and the button is actually disabled (not just
   styled to look that way) so it can't be clicked again mid-request. */
.st-key-refresh_now_button_loading button {{
    position: relative;
    overflow: hidden;
    cursor: progress !important;
    opacity: 1 !important;
    border: none !important;
}}
.st-key-refresh_now_button_loading button [data-testid="stMarkdownContainer"] {{
    position: relative;
    z-index: 1;
    color: #fff !important;
}}
.st-key-refresh_now_button_loading button::before {{
    content: "";
    position: absolute;
    inset: 0;
    background: var(--accent-grad);
    transform: scaleX(0);
    transform-origin: left;
    animation: refresh-btn-fill 1.1s ease-in-out infinite;
}}
@keyframes refresh-btn-fill {{
    0% {{ transform: scaleX(0); }}
    100% {{ transform: scaleX(1); }}
}}
@media (prefers-reduced-motion: reduce) {{
    .st-key-refresh_now_button_loading button::before {{ animation: none; transform: scaleX(1); }}
}}

/* ---------- TEXT INPUTS ---------- */
[data-testid="stTextInput"] input {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: .625rem !important;
    color: var(--text) !important;
    min-height: 2.625rem;
}}
[data-testid="stTextInput"] label p {{
    font-weight: 700 !important;
    opacity: .7;
}}

/* ---------- SEGMENTED CONTROLS (season swatches, EN/BG, degC/degF pills) ---------- */
[data-testid="stSegmentedControl"] div[role="radiogroup"] {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: .625rem;
    padding: .1875rem;
    gap: .125rem;
}}
[data-testid="stSegmentedControl"] label {{
    border-radius: .4375rem !important;
    border: none !important;
    background: transparent !important;
}}
[data-testid="stSegmentedControl"] label p {{
    font-size: .75rem !important;
    font-weight: 700 !important;
    color: var(--text) !important;
}}
[data-testid="stSegmentedControl"] label[aria-checked="true"],
[data-testid="stSegmentedControl"] label:has(input:checked) {{
    background: var(--accent-grad) !important;
}}
[data-testid="stSegmentedControl"] label[aria-checked="true"] p,
[data-testid="stSegmentedControl"] label:has(input:checked) p {{
    color: #fff !important;
}}

/* ---------- TABS ---------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: .375rem;
    border-bottom: 1px solid var(--border);
}}
.stTabs [data-baseweb="tab"] {{
    height: auto;
    padding: .625rem 1.125rem;
    background: transparent !important;
}}
.stTabs [data-baseweb="tab"] p {{
    font-family: 'Manrope', sans-serif !important;
    font-size: .84375rem !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    opacity: .55;
}}
.stTabs [aria-selected="true"] p {{ opacity: 1; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: var(--accent-deep) !important; }}

/* ---------- ALERTS ---------- */
[data-testid="stAlert"] {{
    border-radius: .75rem !important;
    font-weight: 600;
}}
.alert {{ display: flex; align-items: center; gap: .625rem; background: var(--accent-soft); border: 1px solid var(--border); border-radius: .75rem; padding: .6875rem 1rem; margin-bottom: .5rem; }}
.alert .text {{ font-size: .84375rem; font-weight: 600; color: var(--accent-deep); }}
.alert span:first-child {{ cursor: help; }}

/* alert-warning intentionally has no rules of its own -- the base .alert
   styling above is exactly the desired warning-tier look. */
.alert-error {{
    background: var(--alert-error-bg);
    border: 2px solid var(--alert-error-border);
    padding: .625rem 1rem;
    box-shadow: 0 2px 14px var(--alert-error-shadow);
    animation: alert-pulse 2.6s ease-in-out infinite;
}}
.alert-error .text {{ color: var(--alert-error-text); font-weight: 700; font-size: .875rem; }}

@keyframes alert-pulse {{
    0%, 100% {{ box-shadow: 0 2px 14px var(--alert-error-shadow); }}
    50% {{ box-shadow: 0 2px 22px var(--alert-error-shadow-strong); }}
}}
@media (prefers-reduced-motion: reduce) {{
    .alert-error {{ animation: none; }}
}}

/* ---------- WIND SEVERITY ---------- */
/* Applied to the wind reading everywhere it's shown (hero stat chip, hour/day
   cards, 14-day rows) so stronger wind reads as visibly more urgent, the same
   way storm codes get a darker treatment as severity increases. */
.wind-breezy {{ color: var(--wind-breezy); }}
.wind-strong {{ color: var(--wind-strong); font-weight: 700; }}
.wind-severe {{ color: var(--wind-severe); font-weight: 700; }}

/* ---------- APP HEADER ---------- */
.st-key-app_header {{ margin-bottom: 1.375rem; }}
.st-key-app_header [data-testid="stHorizontalBlock"] {{
    align-items: center;
}}
/* Inner control row (season / auto-refresh / language / unit) lives inside col_controls, i.e.
   nested one level deeper than the outer brand/controls split. Let each of its columns shrink
   to fit its actual content instead of stretching to the ratio-based width st.columns() assigns
   by default - that stretching is what left uneven dead-space gaps between the groups. A fixed
   gap on the flex container then gives consistent, tight spacing regardless of content width. */
.st-key-app_header [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] {{
    gap: 1.375rem !important;
    flex-wrap: nowrap;
}}
.st-key-app_header [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    flex: none !important;
    width: auto !important;
    min-width: 0 !important;
}}
.st-key-app_header [data-testid="stCaptionContainer"] {{
    font-size: .6875rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em;
    opacity: .5; color: var(--text); margin-top: .5rem; white-space: nowrap;
}}
.st-key-app_header [data-testid="stSegmentedControl"] div[role="radiogroup"] {{
    padding: .125rem;
}}
.st-key-app_header [data-testid="stSegmentedControl"] label {{
    padding: .25rem .5rem !important;
}}
/* Below the mobile breakpoint, stack the control row (season / auto-refresh / language / unit)
   into four rows in DOM order: season alone, refresh alone, then language + unit sharing a row.
   Scoped to .st-key-header_controls (rather than the unlimited-depth descendant selector above)
   so the refresh row's own nested toggle+button columns aren't caught by the same rule. */
@media (max-width: 640px) {{
    .st-key-header_controls {{
        border-top: 1px solid var(--border);
        padding-top: .75rem;
        margin-top: .75rem;
    }}
    /* Anchored with a direct-child chain (> ... > ...), not an open-ended descendant
       selector, so this only ever matches the season/refresh/lang/unit row itself -
       not the refresh toggle+button row nested several levels deeper inside it,
       which is exactly the ambiguity that made the old rule misbehave. Streamlit
       renders a keyed container's own class on the stVerticalBlock element itself,
       with a stLayoutWrapper as the sole child wrapping the row - verified against
       the live DOM, since this exact chain doesn't otherwise appear elsewhere in
       Streamlit's public docs. */
    .st-key-header_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap !important;
        row-gap: .75rem;
    }}
    /* Season swatches (1st column) and the refresh group (2nd column) each break onto
       their own full-width row; language and unit (3rd/4th) are left to share the row
       that remains, splitting it evenly. */
    .st-key-header_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1),
    .st-key-header_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) {{
        flex-basis: 100% !important;
    }}
    .st-key-header_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3),
    .st-key-header_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) {{
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }}

    /* Refresh row: toggle + button side by side on one line, natural width, no stretch.
       Same direct-child chain as above, rooted at .st-key-refresh_group instead - this
       row is already a flex row via Streamlit's own stHorizontalBlock styling, so only
       flex-wrap/gap need overriding, not display. */
    .st-key-refresh_group > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {{
        flex-wrap: nowrap !important;
        align-items: center;
        gap: .5rem;
    }}
    .st-key-refresh_group > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
        flex: 0 1 auto;
        min-width: 0;
    }}
    .st-key-refresh_group label p {{
        font-size: .75rem;
    }}
    .st-key-refresh_group .stButton button {{
        height: 2rem !important;
        min-height: 2rem !important;
        padding: 0 .625rem !important;
        font-size: .71875rem !important;
    }}
}}
.brand-row {{ display: flex; align-items: center; gap: .875rem; }}
.brand-icon {{
    width: 2.75rem; height: 2.75rem; border-radius: .75rem; background: var(--accent-grad);
    display: flex; align-items: center; justify-content: center; font-size: 1.375rem;
    box-shadow: 0 4px 14px var(--accent-shadow); flex-shrink: 0; cursor: help;
}}
.brand-title {{ font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 1.3125rem; letter-spacing: -.01em; color: var(--text); }}
.brand-sub {{ font-size: .78125rem; opacity: .55; font-weight: 500; color: var(--text); }}

/* ---------- SEARCH / LOCATION CARD ---------- */
.st-key-location_card {{
    background: var(--surface);
    border-radius: 1rem;
    border: 1px solid var(--border);
    box-shadow: 0 2px 12px var(--card-shadow);
    padding: 1.25rem 1.375rem;
}}
.st-key-location_card [data-testid="stVerticalBlockBorderWrapper"] {{
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    background: transparent !important;
}}
.st-key-search_top [data-testid="stHorizontalBlock"] {{
    align-items: center;
    gap: .875rem;
}}
.st-key-search_top [data-testid="stCaptionContainer"] {{
    font-size: .78125rem; font-weight: 400; opacity: .6; color: var(--text);
    text-transform: none; letter-spacing: normal; white-space: nowrap;
}}
.st-key-search_top [data-testid="stCustomComponentV1"] {{
    width: 2.375rem !important; max-width: 2.375rem !important; height: 2.375rem; border-radius: .625rem;
    background: var(--accent-soft);
    border: 1px solid var(--border); overflow: hidden;
}}
.location-divider {{ display: flex; align-items: center; gap: .75rem; }}
.location-divider-line {{ flex: 1; height: .0625rem; background: var(--border); }}
.location-divider-text {{ font-size: .78rem; font-weight: 500; opacity: .55; white-space: nowrap; color: var(--text); }}
.st-key-search_action .stButton button {{ margin-top: 1.6875rem; }}

/* ---------- LOCATION LINE ---------- */
.location {{ display: flex; align-items: baseline; gap: .5rem; margin-bottom: 1rem; }}
.location span:first-child {{ cursor: help; }}
.location .name {{ font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 1.1875rem; color: var(--text); }}

/* ---------- HERO PANEL ---------- */
.hero {{
    background: var(--hero-grad); border: 1px solid var(--border); border-radius: 1.125rem;
    padding: 1.625rem 1.75rem; box-shadow: 0 4px 20px var(--card-shadow); margin-bottom: .25rem;
    display: grid; grid-template-columns: minmax(13.75rem,1fr) 2fr; gap: 1.5rem; align-items: center;
}}
@media (max-width: 760px) {{ .hero {{ grid-template-columns: 1fr; }} }}
.hero-main {{ display: flex; align-items: center; gap: 1rem; }}
.hero-emoji {{ font-size: 3.5rem; line-height: 1; cursor: help; }}
.hero-temp {{ font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 2.75rem; line-height: 1; color: var(--text); }}
.hero-feels {{ font-size: .8125rem; opacity: .65; font-weight: 500; margin-top: .25rem; color: var(--text); }}
.hero-desc {{ font-size: .84375rem; font-weight: 700; color: var(--accent-deep); margin-top: .125rem; }}
.stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(6.875rem, 1fr)); gap: .625rem; }}
.stat-chip {{ background: var(--surface); border: 1px solid var(--border); border-radius: .75rem; padding: .6875rem .75rem; }}
.stat-chip .label {{ font-size: .65625rem; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; opacity: .5; margin-bottom: .25rem; color: var(--text); }}
.stat-chip .value {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 1.0625rem; color: var(--text); }}

/* ---------- 24H GRID ---------- */
.hour-strip {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(5.625rem, 1fr)); gap: .625rem; }}
.hour-card {{ position: relative; background: var(--surface); border: 1px solid var(--border); border-radius: .75rem; padding: .75rem .625rem; text-align: center; }}
.hour-card .time {{ font-size: .71875rem; font-weight: 700; opacity: .6; margin-bottom: .25rem; color: var(--text); }}
.hour-card .emoji {{ font-size: 1.5rem; margin-bottom: .125rem; cursor: help; }}
.hour-card .temp {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: .9375rem; color: var(--text); }}
.hour-card .meta {{ display: flex; flex-direction: column; gap: .125rem; margin-top: .25rem; }}
.hour-card .meta span {{ font-size: .65625rem; opacity: .55; font-weight: 600; color: var(--text); cursor: help; }}
.hour-card .storm-badge {{ top: .25rem; right: .25rem; padding: .0625rem .3125rem; font-size: .5625rem; }}
.hour-card .next-day-badge {{ top: .25rem; left: 50%; transform: translateX(-50%); padding: .0625rem .3125rem; font-size: .5625rem; background: var(--border); color: var(--text); opacity: .75; }}
/* The badge floats above the card's normal flow, so without this the "Tomorrow"
   badge sits right on top of the time label instead of above it. */
.hour-card-next-day .time {{ margin-top: .875rem; }}

.hour-card.hour-card-storm {{ background: var(--storm-bg); border: 1px solid var(--storm-border); box-shadow: 0 4px 14px var(--storm-shadow); }}
.hour-card.hour-card-storm .meta span {{ opacity: .85; }}
.hour-card.hour-card-storm .next-day-badge {{ opacity: .85; }}

.hour-card.hour-card-storm-severe {{ background: var(--storm-severe-bg); border: 2px solid var(--storm-severe-border); box-shadow: 0 8px 22px var(--storm-severe-shadow); }}
.hour-card.hour-card-storm-severe .time,
.hour-card.hour-card-storm-severe .temp {{ color: #fff; }}
.hour-card.hour-card-storm-severe .meta span {{ color: rgba(255,255,255,.85); opacity: 1; }}
.hour-card.hour-card-storm-severe .next-day-badge {{ background: rgba(255,255,255,.85); color: var(--storm-severe-border); opacity: 1; }}

.hour-card-storm .storm-badge {{ background: var(--storm-badge-bg); }}
.hour-card-storm-severe .storm-badge {{ background: var(--storm-severe-border); }}

/* ---------- 7-DAY CARDS ---------- */
.day-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(9.375rem, 1fr)); gap: .75rem; }}
.day-card {{ position: relative; background: var(--surface); border: 1px solid var(--border); border-radius: .875rem; padding: 1rem .875rem; text-align: center; }}
.day-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px var(--card-shadow); }}
.day-card .day {{ font-size: .78125rem; font-weight: 700; margin-bottom: .375rem; color: var(--text); }}
.day-card .emoji {{ font-size: 2rem; margin-bottom: .375rem; cursor: help; }}
.day-card .desc {{ font-size: .71875rem; font-weight: 600; color: var(--accent-deep); margin-bottom: .625rem; min-height: .875rem; }}
.day-card .temps {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: .9375rem; color: var(--text); }}
.day-card .temps .min {{ opacity: .45; font-weight: 600; }}
.day-card .meta {{ display: flex; justify-content: center; gap: .625rem; font-size: .65625rem; opacity: .55; font-weight: 600; margin-top: .5rem; border-top: 1px solid var(--border); padding-top: .5rem; color: var(--text); }}
.day-card .meta span {{ cursor: help; }}

/* ---------- STORM SEVERITY TREATMENT ---------- */
.day-card.day-card-storm {{ background: var(--storm-bg); border: 1px solid var(--storm-border); box-shadow: 0 4px 14px var(--storm-shadow); }}
.day-card.day-card-storm .desc {{ color: var(--text); }}
.day-card.day-card-storm .meta {{ opacity: .85; border-top-color: var(--storm-border); }}
.day-card.day-card-storm .temps .min {{ opacity: .85; }}
.day-card.day-card-storm:hover {{ box-shadow: var(--storm-shadow-hover); }}

.day-card.day-card-storm-severe {{ background: var(--storm-severe-bg); border: 2px solid var(--storm-severe-border); box-shadow: 0 8px 22px var(--storm-severe-shadow); }}
.day-card.day-card-storm-severe .day,
.day-card.day-card-storm-severe .desc,
.day-card.day-card-storm-severe .temps {{ color: #fff; }}
.day-card.day-card-storm-severe .meta,
.day-card.day-card-storm-severe .temps .min {{ color: rgba(255,255,255,.85); opacity: 1; }}
.day-card.day-card-storm-severe .meta {{ border-top-color: rgba(255,255,255,.35); }}
.day-card.day-card-storm-severe:hover {{ box-shadow: var(--storm-severe-shadow-hover); }}

.storm-badge, .next-day-badge {{ position: absolute; border-radius: 999px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }}
.storm-badge {{ top: .5rem; right: .5rem; padding: .125rem .4375rem; font-size: .65625rem; color: #fff; }}
.day-card-storm .storm-badge {{ background: var(--storm-badge-bg); }}
.day-card-storm-severe .storm-badge {{ background: var(--storm-severe-border); }}
.st-key-forecast_tab7 .stButton button {{
    margin-top: .5rem; height: 2rem !important; min-height: 2rem !important; font-size: .71875rem !important;
}}

/* ---------- 14-DAY COMPACT ROWS ---------- */
.st-key-forecast_tab14 {{
    background: var(--surface); border: 1px solid var(--border); border-radius: .875rem; overflow: hidden;
}}
.row-14 {{
    display: grid; grid-template-columns: 6.875rem 2rem 1fr 5.625rem 4.375rem 5rem; align-items: center;
    gap: .75rem; padding: .625rem 1.125rem; border-bottom: 1px solid var(--border);
}}
.row-14 .day {{ font-size: .78125rem; font-weight: 700; color: var(--text); }}
.row-14 .emoji {{ font-size: 1.25rem; cursor: help; }}
.row-14 .desc {{ font-size: .78125rem; font-weight: 600; opacity: .75; color: var(--text); }}
.row-14 .temps {{ font-family: 'Manrope', sans-serif; font-weight: 700; font-size: .84375rem; text-align: right; color: var(--text); }}
.row-14 .temps .min {{ opacity: .45; font-weight: 600; }}
.row-14 .rain, .row-14 .wind {{ font-size: .71875rem; opacity: .6; font-weight: 600; text-align: right; color: var(--text); cursor: help; }}
.st-key-forecast_tab14 .stButton button {{
    height: 2rem !important; min-height: 2rem !important; padding: 0 .625rem !important; font-size: .71875rem !important;
}}
/* The 6 fixed-width grid columns above need ~380px before the flexible 1fr
   column even gets space, which overflows a phone viewport. Below the mobile
   breakpoint, reflow the same six elements into a wrapping flex row instead:
   emoji/day/temps on one line, description on its own line, rain/wind on a third. */
@media (max-width: 640px) {{
    .row-14 {{
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        column-gap: .625rem;
        row-gap: .25rem;
        padding: .75rem 1rem;
    }}
    .row-14 .emoji {{ order: 1; }}
    .row-14 .day {{ order: 2; flex: 1 1 auto; min-width: 0; }}
    .row-14 .temps {{ order: 3; }}
    .row-14 .desc {{ order: 4; flex-basis: 100%; text-align: left; }}
    .row-14 .rain {{ order: 5; text-align: left; }}
    .row-14 .wind {{ order: 6; margin-left: auto; }}
}}

/* ---------- RADAR ---------- */
.radar-frame {{ border-radius: .875rem; overflow: hidden; border: 1px solid var(--border); box-shadow: 0 4px 16px var(--card-shadow); }}
.radar-frame iframe {{ display: block; width: 100%; height: 35rem; border: 0; }}
</style>
"""
