import streamlit as st
import plotly.express as px
from utils.helpers import page_head, section, show_chart, expandable_section, themed
from components.standings import render_team_standings
from components.charts import (
    team_bar_chart,
    team_points_progression,
    driver_contribution_chart,
    qualifying_performance_chart,
    race_pace_chart,
)

TYRE_COLORS = {
    "SOFT":         "#e10600",
    "MEDIUM":       "#ff3333",
    "HARD":         "#666666",
    "INTERMEDIATE": "#990000",
    "WET":          "#cc0000",
}


def render(r_df, l_df, driver_names):
    page_head("Team Standings", "Constructor Championship")

    tab_stand, tab_cmp, tab_analysis = st.tabs([
        "Standings", "Team Comparison", "Race Analysis"
    ])

    # ── Standings ─────────────────────────────────────────────────────────────
    with tab_stand:
        if r_df.empty:
            st.info("No team data yet.")
            return

        team_lim = expandable_section(
            "Constructor", "Standings", "teams_full", preview=4
        )
        render_team_standings(r_df, limit=team_lim)

        st.markdown("<br>", unsafe_allow_html=True)
        show_chart(team_bar_chart(r_df, "Constructor Points", horizontal=True))

    # ── Team Comparison ───────────────────────────────────────────────────────
    with tab_cmp:
        if r_df.empty:
            st.info("No team data yet.")
            return

        all_teams = sorted(r_df["team"].unique().tolist())

        col_a, col_b = st.columns(2)
        with col_a:
            team_a = st.selectbox(
                "Team A", all_teams,
                key="cmp_team_a", index=0,
            )
        with col_b:
            team_b = st.selectbox(
                "Team B", all_teams,
                key="cmp_team_b",
                index=min(1, len(all_teams) - 1),
            )

        if team_a == team_b:
            st.warning("Please select two different teams.")
            return

        st.markdown("<br>", unsafe_allow_html=True)
        section(team_a, "vs " + team_b)

        # Row 1 — points progression + qualifying
        c1, c2 = st.columns(2)
        with c1:
            show_chart(team_points_progression(r_df, [team_a, team_b]))
        with c2:
            show_chart(qualifying_performance_chart(r_df, [team_a, team_b]))

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 2 — driver contribution per team
        c3, c4 = st.columns(2)
        with c3:
            show_chart(driver_contribution_chart(r_df, team_a, driver_names))
        with c4:
            show_chart(driver_contribution_chart(r_df, team_b, driver_names))

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 3 — race pace
        show_chart(race_pace_chart(r_df, [team_a, team_b]))

    # ── Race Analysis ─────────────────────────────────────────────────────────
    with tab_analysis:
        if r_df.empty or l_df.empty:
            st.info("Race data not yet available.")
            return

        races = r_df[["race_id", "race_name"]].drop_duplicates().sort_values("race_id")
        opts  = dict(zip(races["race_name"], races["race_id"]))
        sel   = st.selectbox("Select Race", list(opts.keys()), key="teams_race")
        sid   = opts[sel]

        drivers_in_race = sorted(
            l_df[l_df["race_id"] == sid]["driver"].unique().tolist()
        )
        sel_drivers = st.multiselect(
            "Filter Drivers", drivers_in_race,
            default=drivers_in_race, key="teams_drivers",
        )
        if not sel_drivers:
            sel_drivers = drivers_in_race

        st.markdown("<br>", unsafe_allow_html=True)

        # Tyre usage + degradation
        c1, c2 = st.columns(2)
        with c1:
            tyre = (
                l_df[
                    (l_df["race_id"] == sid) &
                    (l_df["driver"].isin(sel_drivers))
                ]
                .groupby(["driver", "tyre_compound"])
                .size().reset_index(name="laps")
            )
            if not tyre.empty:
                fig = px.bar(
                    tyre, x="driver", y="laps", color="tyre_compound",
                    color_discrete_map=TYRE_COLORS,
                )
                themed(fig, "Tyre Usage")
                fig.update_xaxes(tickangle=45)
                show_chart(fig)

        with c2:
            deg = (
                l_df[
                    (l_df["race_id"] == sid) &
                    l_df["lap_time_secs"].notna() &
                    l_df["driver"].isin(sel_drivers)
                ]
                .groupby(["tyre_compound", "tyre_age"])["lap_time_secs"]
                .mean().reset_index()
            )
            if not deg.empty:
                fig = px.line(
                    deg, x="tyre_age", y="lap_time_secs",
                    color="tyre_compound",
                    color_discrete_map=TYRE_COLORS,
                    labels={
                        "tyre_age": "Tyre Age (laps)",
                        "lap_time_secs": "Avg Lap Time (s)",
                    },
                )
                themed(fig, "Tyre Degradation")
                show_chart(fig)

        st.markdown("<br>", unsafe_allow_html=True)

        # Lap time evolution
        lap_evo = l_df[
            (l_df["race_id"] == sid) &
            l_df["lap_time_secs"].notna() &
            l_df["driver"].isin(sel_drivers)
        ].copy()
        if not lap_evo.empty:
            lap_evo["dname"] = lap_evo["driver"].apply(
                lambda d: driver_names.get(d, (d, "", ""))[0]
            )
            fig = px.line(
                lap_evo, x="lap_number", y="lap_time_secs", color="dname",
                labels={
                    "lap_number": "Lap",
                    "lap_time_secs": "Lap Time (s)",
                    "dname": "Driver",
                },
            )
            themed(fig, "Lap Time Evolution")
            show_chart(fig)

        st.markdown("<br>", unsafe_allow_html=True)

        # Grid vs finish scatter
        scatter_df = r_df[r_df["race_id"] == sid]
        if not scatter_df.empty:
            fig = px.scatter(
                scatter_df, x="grid_pos", y="finish_pos",
                color="driver", text="driver",
                labels={"grid_pos": "Grid", "finish_pos": "Finish"},
            )
            fig.update_traces(textposition="top center", marker=dict(size=10))
            fig.update_yaxes(autorange="reversed")
            fig.update_xaxes(autorange="reversed")
            themed(fig, f"Grid vs Finish — {sel}")
            show_chart(fig)