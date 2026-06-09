import streamlit as st
from utils.helpers import page_head, section, show_chart, expandable_section
from components.standings import render_driver_standings
from components.cards import render_comparison_stats
from components.charts import (
    driver_points_progression,
    driver_finish_trend,
    head_to_head_bar,
    driver_bar_chart,
)


def _driver_stats(r_df, driver: str) -> dict:
    sub = r_df[r_df["driver"] == driver]
    if sub.empty:
        return {}
    return {
        "points":     int(sub["total_points"].sum()),
        "wins":       int((sub["finish_pos"] == 1).sum()),
        "podiums":    int((sub["finish_pos"] <= 3).sum()),
        "avg_finish": round(float(sub["finish_pos"].mean()), 1),
        "avg_grid":   round(float(sub["grid_pos"].mean()), 1),
    }


def render(r_df, driver_names):
    page_head("Driver Standings", "Season Overview")

    tab_stand, tab_cmp = st.tabs(["Standings", "Driver Comparison"])

    # ── Standings tab ─────────────────────────────────────────────────────────
    with tab_stand:
        if r_df.empty:
            st.info("No race data yet.")
            return

        drv_lim = expandable_section("Driver", "Standings", "drivers_full", preview=4)
        render_driver_standings(r_df, driver_names, limit=drv_lim)

        st.markdown("<br>", unsafe_allow_html=True)
        show_chart(driver_bar_chart(r_df, driver_names, "Driver Points"))

        st.markdown("<br>", unsafe_allow_html=True)
        top5 = (
            r_df.groupby("driver")["total_points"].sum()
            .nlargest(5).index.tolist()
        )
        show_chart(driver_points_progression(r_df, driver_names, top5))

    # ── Comparison tab ────────────────────────────────────────────────────────
    with tab_cmp:
        if r_df.empty:
            st.info("No race data yet.")
            return

        all_drivers = sorted(r_df["driver"].unique().tolist())

        col_a, col_b = st.columns(2)
        with col_a:
            drv_a = st.selectbox(
                "Driver A",
                all_drivers,
                format_func=lambda d: f"{driver_names.get(d, (d,'',''))[0]} ({d})",
                key="cmp_drv_a",
                index=0,
            )
        with col_b:
            drv_b = st.selectbox(
                "Driver B",
                all_drivers,
                format_func=lambda d: f"{driver_names.get(d, (d,'',''))[0]} ({d})",
                key="cmp_drv_b",
                index=min(1, len(all_drivers) - 1),
            )

        if drv_a == drv_b:
            st.warning("Please select two different drivers.")
            return

        stats_a = _driver_stats(r_df, drv_a)
        stats_b = _driver_stats(r_df, drv_b)

        st.markdown("<br>", unsafe_allow_html=True)

        # Stat comparison cards
        name_a = driver_names.get(drv_a, (drv_a, ""))[0]
        name_b = driver_names.get(drv_b, (drv_b, ""))[0]
        section(name_a, "vs " + name_b)
        render_comparison_stats(stats_a, stats_b)

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts row 1
        c1, c2 = st.columns(2)
        with c1:
            show_chart(driver_points_progression(r_df, driver_names, [drv_a, drv_b]))
        with c2:
            show_chart(driver_finish_trend(r_df, driver_names, [drv_a, drv_b]))

        st.markdown("<br>", unsafe_allow_html=True)

        # Head to head bar
        show_chart(head_to_head_bar(stats_a, stats_b, drv_a, drv_b, driver_names))