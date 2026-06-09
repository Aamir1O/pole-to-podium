import streamlit as st
from utils.helpers import page_head, section, show_chart, render_html_block
from components.charts import (
    lap_time_evolution,
    tyre_degradation_chart,
    tyre_usage_chart,
    position_changes_chart,
    qualifying_vs_race_scatter,
    race_pace_analysis,
)


def render(r_df, l_df, driver_names):
    page_head("Analytics", "Race Analysis")

    if r_df.empty or l_df.empty:
        st.info("Race data not yet available.")
        return

    # ── Race + driver selectors ───────────────────────────────────────────────
    races = (
        r_df[["race_id", "race_name"]]
        .drop_duplicates()
        .sort_values("race_id", ascending=False)
    )
    opts = dict(zip(races["race_name"], races["race_id"]))

    sel_col, drv_col = st.columns([1, 2])

    with sel_col:
        sel_race = st.selectbox(
            "Select Race", list(opts.keys()),
            key="analytics_race",
        )

    race_id         = opts[sel_race]
    drivers_in_race = sorted(
        l_df[l_df["race_id"] == race_id]["driver"].unique().tolist()
    )

    with drv_col:
        sel_drivers = st.multiselect(
            "Filter Drivers", drivers_in_race,
            default=drivers_in_race[:8],
            key="analytics_drivers",
        )

    if not sel_drivers:
        sel_drivers = drivers_in_race

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 1: Lap time evolution + Position changes ──────────────────────────
    section("Lap Time", "Analysis")

    c1, c2 = st.columns(2)
    with c1:
        fig = lap_time_evolution(l_df, race_id, sel_drivers, driver_names)
        if fig is not None:
            show_chart(fig)

    with c2:
        fig = position_changes_chart(r_df, race_id)
        if fig is not None:
            show_chart(fig)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: Tyre strategy + Tyre degradation ───────────────────────────────
    section("Tyre", "Strategy")

    c3, c4 = st.columns(2)
    with c3:
        fig = tyre_usage_chart(l_df, race_id, sel_drivers)
        if fig is not None:
            show_chart(fig)

    with c4:
        fig = tyre_degradation_chart(l_df, race_id, sel_drivers)
        if fig is not None:
            show_chart(fig)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 3: Qualifying vs Race + Race pace distribution ────────────────────
    section("Performance", "Insights")

    c5, c6 = st.columns(2)
    with c5:
        fig = qualifying_vs_race_scatter(r_df, race_id)
        if fig is not None:
            show_chart(fig)

    with c6:
        fig = race_pace_analysis(l_df, race_id, sel_drivers, driver_names)
        if fig is not None:
            show_chart(fig)