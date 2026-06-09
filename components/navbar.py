import streamlit as st
from utils.helpers import render_html_block, esc

F1_LOGO_SVG = (
    '<svg class="f1-logo-svg" viewBox="0 0 52 22" xmlns="http://www.w3.org/2000/svg">'
    '<text x="1" y="18" fill="#ffffff" font-family="Arial Black,Arial,sans-serif" '
    'font-size="22" font-weight="900" font-style="italic">F</text>'
    '<text x="17" y="18" fill="#e10600" font-family="Arial Black,Arial,sans-serif" '
    'font-size="22" font-weight="900" font-style="italic">1</text>'
    '</svg>'
)

NAV_ITEMS = [
    ("dashboard",   "Dashboard"),
    ("drivers",     "Drivers"),
    ("teams",       "Teams"),
    ("predictions", "Predictions"),
    ("analytics",   "Analytics"),
    ("archive",     "Archive"),
]


def render_navbar(next_name: str, current_page: str) -> None:
    """Renders the logo + next race pill. Navigation buttons are rendered separately."""
    render_html_block(
        f'<div class="p2p-navbar fade-up">'
        f'  <div class="p2p-logo">'
        f'    <div class="logo-icon">{F1_LOGO_SVG}</div>'
        f'    <span class="logo-text">Pole</span>'
        f'    <span class="logo-accent">&nbsp;to&nbsp;</span>'
        f'    <span class="logo-text">Podium</span>'
        f'  </div>'
        f'  <div class="p2p-nav-divider"></div>'
        f'  <div class="p2p-next-race">'
        f'    <span class="nr-flag">Next Race</span>'
        f'    <span class="nr-name">{esc(next_name)}</span>'
        f'  </div>'
        f'</div>'
    )


def render_nav_buttons() -> None:
    """
    Renders real Streamlit buttons for navigation.
    Each button sets st.session_state.page and calls st.rerun().
    """
    current = st.session_state.get("page", "dashboard")

    # inject button styling so they look like nav links
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div {
        padding: 0 !important;
    }
    div.nav-row button {
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0 !important;
        color: #666 !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.04em !important;
        padding: 0.45rem 0.6rem !important;
        width: 100% !important;
        transition: color 0.15s !important;
    }
    div.nav-row button:hover {
        color: #ccc !important;
        background: transparent !important;
        border-bottom: 2px solid #333 !important;
    }
    div.nav-row button[kind="primary"] {
        color: #fff !important;
        border-bottom: 2px solid #e10600 !important;
        font-weight: 700 !important;
    }
    div.nav-row { border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="nav-row">', unsafe_allow_html=True)
    cols = st.columns(len(NAV_ITEMS))
    for col, (key, label) in zip(cols, NAV_ITEMS):
        with col:
            kind = "primary" if current == key else "secondary"
            if st.button(label, key=f"nav_{key}", type=kind, use_container_width=True):
                st.session_state.page = key
                # clear any subpage state when navigating
                st.session_state.pop("subpage", None)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)