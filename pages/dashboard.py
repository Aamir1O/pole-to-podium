import streamlit as st
from utils.helpers import page_head, section, show_chart, render_html_block, esc
from components.cards import render_hero_stats, render_race_cards
from components.standings import render_driver_standings, render_team_standings
from components.charts import (
    championship_battle_chart,
    driver_bar_chart,
    team_bar_chart,
    win_prob_chart,
    win_distribution_pie,
    pole_to_win_gauge,
)


def _section_header(title: str, accent: str, btn_label: str, btn_key: str, subpage: str) -> None:
    """Renders section title + button on the same line using HTML + a Streamlit button trick."""
    render_html_block(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'margin:1.4rem 0 0.85rem;">'
        f'<div class="p2p-section-title" style="margin:0;">'
        f'{esc(title)} <span>{esc(accent)}</span>'
        f'</div>'
        f'<button class="p2p-inline-btn" '
        f'onclick="window.parent.document.querySelector(\'[data-testid=\\\"stButton\\\"] '
        f'button[key=\\\"{btn_key}\\\"]\').click()" '
        f'style="background:transparent;border:none;color:#e10600;font-size:0.72rem;'
        f'font-weight:600;cursor:pointer;font-family:inherit;padding:0;line-height:1;">'
        f'{esc(btn_label)}'
        f'</button>'
        f'</div>'
    )
    # Hidden Streamlit button that actually fires the rerun
    if st.button(btn_label, key=btn_key, type="tertiary"):
        st.session_state.subpage = subpage
        st.rerun()


def render(r_df, q_df, l_df, w_df, results_all, laps_all,
           driver_names, next_name, next_circuit,
           pred_fn, le_driver, le_team, le_circuit, features, model):

    page_head("Dashboard", "2026 Season Overview")

    # ── Hero metrics ──────────────────────────────────────────────────────────
    if not r_df.empty:
        render_hero_stats(r_df, driver_names)

    # ── Championship Battle — hero chart ──────────────────────────────────────
    if not r_df.empty:
        render_html_block(
            '<div class="p2p-chart-hero fade-up">'
            '<div class="p2p-chart-hero-title">'
            'Championship <span>Battle</span>'
            '</div>'
        )
        show_chart(championship_battle_chart(r_df, driver_names, top_n=5))
        render_html_block('</div>')
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Build prediction once for reuse ───────────────────────────────────────
    pred_mini      = None
    latest_race_id = q_df["race_id"].max() if not q_df.empty else None

    if latest_race_id and not r_df.empty:
        ri   = r_df[r_df["race_id"] == latest_race_id]
        circ = ri["circuit"].iloc[0] if not ri.empty else next_circuit
        try:
            pred_mini = pred_fn(
                results_all, laps_all, q_df, w_df,
                latest_race_id, circ,
                le_driver=le_driver, le_team=le_team,
                le_circuit=le_circuit, features=features, model=model,
            )
        except Exception:
            pred_mini = None

    # ── Row 1: Driver Standings + Race Schedule ───────────────────────────────
    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        render_html_block(
            '<div style="display:flex;align-items:center;justify-content:space-between;'
            'margin:1.4rem 0 0.6rem;">'
            '<div class="p2p-section-title" style="margin:0;">Driver <span>Standings</span></div>'
            '</div>'
        )
        col_spacer, col_btn = st.columns([5, 1])
        with col_btn:
            if st.button("See full →", key="dash_sub_drivers", type="tertiary"):
                st.session_state.subpage = "all_drivers"
                st.rerun()

        if not r_df.empty:
            render_driver_standings(
                r_df, driver_names, next_name,
                show_pred_bar=True,
                pred_df=pred_mini,
                limit=4,
            )
        else:
            render_html_block(
                '<div style="color:#444;font-size:0.85rem;padding:1rem 0;">'
                'No driver data available yet.</div>'
            )

    with col_right:
        render_html_block(
            '<div style="display:flex;align-items:center;justify-content:space-between;'
            'margin:1.4rem 0 0.6rem;">'
            '<div class="p2p-section-title" style="margin:0;">Race <span>Schedule</span></div>'
            '</div>'
        )
        col_spacer2, col_btn2 = st.columns([5, 1])
        with col_btn2:
            if st.button("See all →", key="dash_sub_races", type="tertiary"):
                st.session_state.subpage = "all_races"
                st.rerun()

        if not r_df.empty:
            render_race_cards(r_df, driver_names, limit=4)
        else:
            render_html_block(
                '<div style="color:#444;font-size:0.85rem;padding:1rem 0;">'
                'No race data available yet.</div>'
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: Constructor Standings + Win Probability Preview ────────────────
    col2_left, col2_right = st.columns([1.1, 0.9])

    with col2_left:
        render_html_block(
            '<div style="display:flex;align-items:center;justify-content:space-between;'
            'margin:1.4rem 0 0.6rem;">'
            '<div class="p2p-section-title" style="margin:0;">Constructor <span>Standings</span></div>'
            '</div>'
        )
        col_spacer3, col_btn3 = st.columns([5, 1])
        with col_btn3:
            if st.button("See full →", key="dash_sub_teams", type="tertiary"):
                st.session_state.subpage = "all_teams"
                st.rerun()

        if not r_df.empty:
            render_team_standings(r_df, limit=4)
        else:
            render_html_block(
                '<div style="color:#444;font-size:0.85rem;padding:1rem 0;">'
                'No team data available yet.</div>'
            )

    with col2_right:
        if pred_mini is not None and not pred_mini.empty:
            section("Win Probability", "Preview")
            fig = win_prob_chart(
                pred_mini, driver_names,
                title=f"Win Probability — {next_name}",
            )
            fig.update_layout(height=300)
            show_chart(fig)

    # ── Analytics summary (collapsed) ─────────────────────────────────────────
    if not r_df.empty:
        st.markdown("<br>", unsafe_allow_html=True)

        expand_key = "dash_analytics_expanded"
        if expand_key not in st.session_state:
            st.session_state[expand_key] = False

        render_html_block(
            '<div style="display:flex;align-items:center;justify-content:space-between;'
            'margin:1.4rem 0 0.6rem;">'
            '<div class="p2p-section-title" style="margin:0;">Analytics <span>Charts</span></div>'
            '</div>'
        )
        col_spacer4, col_btn4 = st.columns([5, 1])
        with col_btn4:
            label = "Show less ↑" if st.session_state[expand_key] else "Expand →"
            if st.button(label, key="dash_analytics_btn", type="tertiary"):
                st.session_state[expand_key] = not st.session_state[expand_key]
                st.rerun()

        if not st.session_state.get(expand_key, False):
            render_html_block(
                '<div style="color:#444;font-size:0.75rem;padding:0.2rem 0 0.4rem;">'
                'Click <span style="color:#e10600;">Expand →</span> '
                'to view season analytics.</div>'
            )
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            ch1, ch2 = st.columns(2)
            with ch1:
                show_chart(driver_bar_chart(r_df, driver_names, "Driver Standings"))
            with ch2:
                show_chart(team_bar_chart(r_df, "Constructor Standings"))
            ch3, ch4 = st.columns(2)
            with ch3:
                show_chart(win_distribution_pie(r_df, driver_names))
            with ch4:
                show_chart(pole_to_win_gauge(r_df))