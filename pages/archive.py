import streamlit as st
from utils.helpers import page_head, section, show_chart, render_html_block
from components.cards import render_race_cards, render_comparison_stats
from components.standings import render_driver_standings, render_team_standings
from components.charts import (
    championship_battle_chart,
    driver_bar_chart,
    team_bar_chart,
    win_distribution_pie,
    pole_to_win_gauge,
    driver_points_progression,
    driver_finish_trend,
    head_to_head_bar,
    lap_time_evolution,
    tyre_degradation_chart,
    tyre_usage_chart,
)

TYRE_COLORS = {
    "SOFT":         "#e10600",
    "MEDIUM":       "#ff3333",
    "HARD":         "#666666",
    "INTERMEDIATE": "#990000",
    "WET":          "#cc0000",
}


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


def render(r_df, l_df, driver_names):
    page_head("2025 Season Archive", "Final standings and race analysis — 24 races complete")

    if r_df.empty:
        st.info("No 2025 data available.")
        return

    pts_col = "total_points"

    tab1, tab2, tab3, tab4 = st.tabs([
        "Final Standings",
        "Race Results",
        "Tyre & Strategy",
        "Driver Stats",
    ])

    # ── Tab 1: Final Standings ────────────────────────────────────────────────
    with tab1:
        c1, c2 = st.columns(2)

        with c1:
            section("Driver", "Championship")
            render_driver_standings(r_df, driver_names, show_pred_bar=False)

        with c2:
            section("Constructor", "Championship")
            render_team_standings(r_df)

        st.markdown("<br>", unsafe_allow_html=True)

        show_chart(championship_battle_chart(r_df, driver_names, top_n=5))

        st.markdown("<br>", unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        with c3:
            dp = r_df.groupby("driver")[pts_col].sum().reset_index().sort_values(pts_col, ascending=False)
            dp["dname"] = dp["driver"].apply(lambda d: driver_names.get(d, (d, ""))[0])
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(
                x=dp["dname"], y=dp[pts_col],
                marker=dict(
                    color=dp[pts_col],
                    colorscale=[[0, "#330000"], [1, "#e10600"]],
                    showscale=False,
                ),
                text=dp[pts_col].astype(int), textposition="outside",
            ))
            from utils.helpers import themed
            themed(fig, "Final Driver Championship (WDC)")
            fig.update_xaxes(tickangle=45)
            show_chart(fig)

        with c4:
            tp = r_df.groupby("team")[pts_col].sum().reset_index().sort_values(pts_col, ascending=False)
            fig = go.Figure(go.Bar(
                x=tp["team"], y=tp[pts_col],
                marker=dict(color=tp[pts_col], colorscale=[[0, "#330000"], [1, "#ff3333"]], showscale=False),
                text=tp[pts_col].astype(int), textposition="outside",
            ))
            themed(fig, "Final Constructor Championship (WCC)")
            fig.update_xaxes(tickangle=30)
            show_chart(fig)

        st.markdown("<br>", unsafe_allow_html=True)

        c5, c6 = st.columns(2)
        with c5:
            show_chart(win_distribution_pie(r_df, driver_names))
        with c6:
            show_chart(pole_to_win_gauge(r_df))

    # ── Tab 2: Race Results ───────────────────────────────────────────────────
    with tab2:
        section("Race", "Winners")
        render_race_cards(r_df, driver_names, limit=24)

        st.markdown("<br>", unsafe_allow_html=True)

        import plotly.express as px
        fig = px.scatter(
            r_df, x="grid_pos", y="finish_pos", color="driver",
            hover_data=["race_name", "team"],
            labels={"grid_pos": "Grid", "finish_pos": "Finish", "driver": "Driver"},
            opacity=0.75,
            color_discrete_sequence=["#e10600","#ff3333","#cc0000","#990000","#660000",
                                      "#ff6666","#cc3333","#aa0000","#882222","#551111"],
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(autorange="reversed")
        from utils.helpers import themed
        themed(fig, "Grid vs Finish Position — 2025")
        show_chart(fig)

    # ── Tab 3: Tyre & Strategy ────────────────────────────────────────────────
    with tab3:
        if l_df.empty:
            st.info("Lap data not available.")
        else:
            races_25 = r_df[["race_id", "race_name"]].drop_duplicates().sort_values("race_id")
            opts_25  = dict(zip(races_25["race_name"], races_25["race_id"]))
            sel25    = st.selectbox("Select Race", list(opts_25.keys()), key="archive_sel25")
            sid25    = opts_25[sel25]

            drivers_25_race = sorted(l_df[l_df["race_id"] == sid25]["driver"].unique().tolist())
            sel_d25 = st.multiselect(
                "Filter Drivers", drivers_25_race,
                default=drivers_25_race, key="archive_strat_drivers25",
            )
            if not sel_d25:
                sel_d25 = drivers_25_race

            st.markdown("<br>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                fig = tyre_usage_chart(l_df, sid25, sel_d25)
                if fig:
                    show_chart(fig)
            with c2:
                fig = tyre_degradation_chart(l_df, sid25, sel_d25)
                if fig:
                    show_chart(fig)

            st.markdown("<br>", unsafe_allow_html=True)

            fig = lap_time_evolution(l_df, sid25, sel_d25, driver_names)
            if fig:
                show_chart(fig)

            st.markdown("<br>", unsafe_allow_html=True)

            # Winner strategy
            wd25 = r_df[r_df["race_id"] == sid25].sort_values("finish_pos")
            if not wd25.empty:
                wdrv  = wd25["driver"].iloc[0]
                wname = driver_names.get(wdrv, (wdrv, "", ""))[0]
                section("Winner Strategy", wname)

                wlaps25 = l_df[
                    (l_df["race_id"] == sid25) &
                    (l_df["driver"] == wdrv) &
                    l_df["lap_time_secs"].notna()
                ]
                if not wlaps25.empty:
                    import plotly.express as px
                    fig = px.scatter(
                        wlaps25, x="lap_number", y="lap_time_secs",
                        color="tyre_compound", color_discrete_map=TYRE_COLORS,
                    )
                    from utils.helpers import themed
                    themed(fig, "Lap Times by Tyre Compound")
                    show_chart(fig)

    # ── Tab 4: Driver Stats ───────────────────────────────────────────────────
    with tab4:
        d_opts  = sorted(r_df["driver"].unique())
        sel_drv = st.multiselect(
            "Select Drivers", d_opts,
            default=d_opts[:5], key="archive_drv25_stats",
        )

        if not sel_drv:
            st.info("Select at least one driver.")
            return

        st.markdown("<br>", unsafe_allow_html=True)

        # Avg lap time + total points
        c1, c2 = st.columns(2)
        with c1:
            if not l_df.empty:
                avg25 = (
                    l_df[l_df["driver"].isin(sel_drv) & l_df["lap_time_secs"].notna()]
                    .groupby("driver")["lap_time_secs"].mean()
                    .reset_index().sort_values("lap_time_secs")
                )
                avg25["dname"] = avg25["driver"].apply(
                    lambda d: driver_names.get(d, (d, "", ""))[0]
                )
                import plotly.graph_objects as go
                fig = go.Figure(go.Bar(
                    x=avg25["dname"], y=avg25["lap_time_secs"],
                    marker_color="#e10600",
                    text=avg25["lap_time_secs"].round(2), textposition="outside",
                    textfont=dict(size=10, color="#666"),
                ))
                from utils.helpers import themed
                themed(fig, "Avg Lap Time (lower = faster)")
                show_chart(fig)

        with c2:
            pts25 = (
                r_df[r_df["driver"].isin(sel_drv)]
                .groupby("driver")["total_points"].sum()
                .reset_index().sort_values("total_points", ascending=False)
            )
            pts25["dname"] = pts25["driver"].apply(
                lambda d: driver_names.get(d, (d, "", ""))[0]
            )
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(
                x=pts25["dname"], y=pts25["total_points"],
                marker_color="#ff3333",
                text=pts25["total_points"].astype(int), textposition="outside",
                textfont=dict(size=10, color="#666"),
            ))
            from utils.helpers import themed
            themed(fig, "Total Points 2025")
            show_chart(fig)

        st.markdown("<br>", unsafe_allow_html=True)

        # Points progression
        show_chart(driver_points_progression(r_df, driver_names, sel_drv))

        st.markdown("<br>", unsafe_allow_html=True)

        # Finishing trend
        show_chart(driver_finish_trend(r_df, driver_names, sel_drv))

        st.markdown("<br>", unsafe_allow_html=True)

        # Head-to-head (only when exactly 2 drivers selected)
        if len(sel_drv) == 2:
            drv_a, drv_b = sel_drv[0], sel_drv[1]
            stats_a = _driver_stats(r_df, drv_a)
            stats_b = _driver_stats(r_df, drv_b)
            name_a  = driver_names.get(drv_a, (drv_a, ""))[0]
            name_b  = driver_names.get(drv_b, (drv_b, ""))[0]
            section(name_a, "vs " + name_b)
            render_comparison_stats(stats_a, stats_b)
            st.markdown("<br>", unsafe_allow_html=True)
            show_chart(head_to_head_bar(stats_a, stats_b, drv_a, drv_b, driver_names))