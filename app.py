import streamlit as st
from styles.theme import inject_styles
from utils.data import load_data, filter_season
from utils.predictions import load_model, build_predictions
from utils.helpers import render_html_block
from components.navbar import render_navbar, render_nav_buttons

import pages.dashboard   as page_dashboard
import pages.drivers     as page_drivers
import pages.teams       as page_teams
import pages.predictions as page_predictions
import pages.analytics   as page_analytics
import pages.archive     as page_archive

from datetime import datetime, timezone
import pytz

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pole to Podium",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_styles()
st.markdown("""
<style>
body {
    background: green !important;
}
</style>
""", unsafe_allow_html=True)

# ── metadata ──────────────────────────────────────────────────────────────────
DRIVER_NAMES = {
    "ANT": ("Kimi Antonelli",    "ITA", "#e10600"),
    "RUS": ("George Russell",    "GBR", "#e10600"),
    "HAM": ("Lewis Hamilton",    "GBR", "#ff3333"),
    "LEC": ("Charles Leclerc",   "MON", "#ff3333"),
    "NOR": ("Lando Norris",      "GBR", "#cc0000"),
    "PIA": ("Oscar Piastri",     "AUS", "#cc0000"),
    "VER": ("Max Verstappen",    "NED", "#990000"),
    "HAD": ("Isack Hadjar",      "FRA", "#990000"),
    "LAW": ("Liam Lawson",       "NZL", "#b30000"),
    "LIN": ("Arvid Lindblad",    "GBR", "#b30000"),
    "GAS": ("Pierre Gasly",      "FRA", "#800000"),
    "COL": ("Franco Colapinto",  "ARG", "#800000"),
    "BEA": ("Oliver Bearman",    "GBR", "#666666"),
    "OCO": ("Esteban Ocon",      "FRA", "#666666"),
    "SAI": ("Carlos Sainz",      "ESP", "#ff6666"),
    "ALB": ("Alexander Albon",   "THA", "#ff6666"),
    "BOR": ("Gabriel Bortoleto", "BRA", "#e10600"),
    "HUL": ("Nico Hulkenberg",   "GER", "#e10600"),
    "BOT": ("Valtteri Bottas",   "FIN", "#aa0000"),
    "PER": ("Sergio Perez",      "MEX", "#aa0000"),
    "STR": ("Lance Stroll",      "CAN", "#770000"),
    "ALO": ("Fernando Alonso",   "ESP", "#770000"),
}

UPCOMING_RACES = [
    {"name": "Spanish Grand Prix",       "circuit": "Barcelona-Catalunya", "dt": "2026-06-14 13:00", "tz": "Europe/Madrid"},
    {"name": "Austrian Grand Prix",      "circuit": "Spielberg",           "dt": "2026-06-28 13:00", "tz": "Europe/Vienna"},
    {"name": "British Grand Prix",       "circuit": "Silverstone",         "dt": "2026-07-05 13:00", "tz": "Europe/London"},
    {"name": "Belgian Grand Prix",       "circuit": "Spa-Francorchamps",   "dt": "2026-07-19 13:00", "tz": "Europe/Brussels"},
    {"name": "Hungarian Grand Prix",     "circuit": "Budapest",            "dt": "2026-07-26 13:00", "tz": "Europe/Budapest"},
    {"name": "Dutch Grand Prix",         "circuit": "Zandvoort",           "dt": "2026-08-23 13:00", "tz": "Europe/Amsterdam"},
    {"name": "Italian Grand Prix",       "circuit": "Monza",               "dt": "2026-09-06 13:00", "tz": "Europe/Rome"},
    {"name": "Azerbaijan Grand Prix",    "circuit": "Baku",                "dt": "2026-09-26 12:00", "tz": "Asia/Baku"},
    {"name": "Singapore Grand Prix",     "circuit": "Marina Bay",          "dt": "2026-10-11 13:00", "tz": "Asia/Singapore"},
    {"name": "United States Grand Prix", "circuit": "Austin",              "dt": "2026-10-25 19:00", "tz": "America/Chicago"},
    {"name": "Mexico City Grand Prix",   "circuit": "Mexico City",         "dt": "2026-11-01 20:00", "tz": "America/Mexico_City"},
    {"name": "São Paulo Grand Prix",     "circuit": "São Paulo",           "dt": "2026-11-08 17:00", "tz": "America/Sao_Paulo"},
    {"name": "Las Vegas Grand Prix",     "circuit": "Las Vegas",           "dt": "2026-11-21 06:00", "tz": "America/Los_Angeles"},
    {"name": "Qatar Grand Prix",         "circuit": "Lusail",              "dt": "2026-11-29 17:00", "tz": "Asia/Qatar"},
    {"name": "Abu Dhabi Grand Prix",     "circuit": "Yas Island",          "dt": "2026-12-06 13:00", "tz": "Asia/Dubai"},
]

def get_next_race():
    now = datetime.now(timezone.utc)
    for r in UPCOMING_RACES:
        tz      = pytz.timezone(r["tz"])
        race_dt = tz.localize(
            datetime.strptime(r["dt"], "%Y-%m-%d %H:%M")
        ).astimezone(timezone.utc)
        if race_dt > now:
            return r["name"], r["circuit"]
    return "Season Complete", ""

# ── load data once ─────────────────────────────────────────────────────────────
results_all, qualifying_all, laps_all, weather_all = load_data()
model, enc = load_model()

le_driver  = enc["driver"]
le_team    = enc["team"]
le_circuit = enc["circuit"]
features   = enc["features"]

r26, q26, l26, w26 = filter_season(results_all, qualifying_all, laps_all, weather_all, 2026)
r25, q25, l25, w25 = filter_season(results_all, qualifying_all, laps_all, weather_all, 2025)

next_name, next_circuit = get_next_race()

# ── session state init ─────────────────────────────────────────────────────────
if "page"    not in st.session_state:
    st.session_state.page    = "dashboard"
if "subpage" not in st.session_state:
    st.session_state.subpage = None

# ── navbar (logo + next race pill) ────────────────────────────────────────────
render_navbar(next_name, st.session_state.page)

# ── nav buttons (these actually work) ─────────────────────────────────────────
render_nav_buttons()

page    = st.session_state.page
subpage = st.session_state.get("subpage")

# ── subpage: full driver standings ────────────────────────────────────────────
if subpage == "all_drivers":
    from utils.helpers import page_head, section
    from components.standings import render_driver_standings

    col_back, _ = st.columns([1, 6])
    with col_back:
        if st.button("← Back", key="back_drivers"):
            st.session_state.subpage = None
            st.rerun()

    page_head("Driver Standings", "2026 Season — Full standings")
    render_driver_standings(r26, DRIVER_NAMES, next_name, show_pred_bar=False)

# ── subpage: full constructor standings ───────────────────────────────────────
elif subpage == "all_teams":
    from utils.helpers import page_head
    from components.standings import render_team_standings
    from components.charts import team_bar_chart
    from utils.helpers import show_chart

    col_back, _ = st.columns([1, 6])
    with col_back:
        if st.button("← Back", key="back_teams"):
            st.session_state.subpage = None
            st.rerun()

    page_head("Constructor Standings", "2026 Season — Full standings")
    render_team_standings(r26)
    st.markdown("<br>", unsafe_allow_html=True)
    show_chart(team_bar_chart(r26, "Constructor Points 2026", horizontal=True))

# ── subpage: full race schedule ───────────────────────────────────────────────
elif subpage == "all_races":
    from utils.helpers import page_head
    from components.cards import render_race_cards

    col_back, _ = st.columns([1, 6])
    with col_back:
        if st.button("← Back", key="back_races"):
            st.session_state.subpage = None
            st.rerun()

    page_head("Race Schedule", "2026 Season — All races")
    render_race_cards(r26, DRIVER_NAMES, limit=30)

# ── main pages ────────────────────────────────────────────────────────────────
elif page == "dashboard":
    page_dashboard.render(
        r_df=r26, q_df=q26, l_df=l26, w_df=w26,
        results_all=results_all, laps_all=laps_all,
        driver_names=DRIVER_NAMES,
        next_name=next_name, next_circuit=next_circuit,
        pred_fn=build_predictions,
        le_driver=le_driver, le_team=le_team,
        le_circuit=le_circuit, features=features, model=model,
    )

elif page == "drivers":
    page_drivers.render(r_df=r26, driver_names=DRIVER_NAMES)

elif page == "teams":
    page_teams.render(r_df=r26, l_df=l26, driver_names=DRIVER_NAMES)

elif page == "predictions":
    page_predictions.render(
        r_df=r26, q_df=q26, l_df=l26, w_df=w26,
        results_all=results_all, laps_all=laps_all,
        driver_names=DRIVER_NAMES,
        next_name=next_name, next_circuit=next_circuit,
        pred_fn=build_predictions,
        le_driver=le_driver, le_team=le_team,
        le_circuit=le_circuit, features=features, model=model,
    )

elif page == "analytics":
    page_analytics.render(r_df=r26, l_df=l26, driver_names=DRIVER_NAMES)

elif page == "archive":
    page_archive.render(r_df=r25, l_df=l25, driver_names=DRIVER_NAMES)

# ── footer ─────────────────────────────────────────────────────────────────────
render_html_block(
    '<div class="p2p-footer fade-up">'
    'Pole to Podium · Built by Aamir · '
    '</div>'
)