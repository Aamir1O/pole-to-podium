import plotly.express as px
import plotly.graph_objects as go
from backend.utils.helpers import themed

RED_SCALE = [
    "#e10600", "#ff3333", "#cc0000", "#990000", "#660000",
    "#ff6666", "#cc3333", "#aa0000", "#882222", "#551111",
]

TYRE_COLORS = {
    "SOFT":         "#e10600",
    "MEDIUM":       "#ff3333",
    "HARD":         "#666666",
    "INTERMEDIATE": "#990000",
    "WET":          "#cc0000",
}


# ── Season / Championship ────────────────────────────────────────────────────

def championship_battle_chart(r_df, driver_names, top_n=5):
    top  = r_df.groupby("driver")["total_points"].sum().nlargest(top_n).index.tolist()
    prog = r_df[r_df["driver"].isin(top)].sort_values("race_id").copy()
    prog["cumpts"] = prog.groupby("driver")["total_points"].cumsum()
    prog["dname"]  = prog["driver"].apply(lambda d: driver_names.get(d, (d, "", ""))[0])
    fig = px.line(
        prog, x="race_id", y="cumpts", color="dname",
        labels={"race_id": "Round", "cumpts": "Points", "dname": "Driver"},
        color_discrete_sequence=RED_SCALE,
    )
    fig.update_traces(
        line=dict(width=2.5),
        mode="lines+markers",
        marker=dict(size=5, symbol="circle"),
    )
    themed(fig, f"Championship Battle — Top {top_n}")
    fig.update_xaxes(tickangle=45, tickfont=dict(size=9))
    fig.update_layout(
        height=380,
        legend=dict(orientation="h", y=-0.22, x=0, font=dict(size=11)),
    )
    return fig


def driver_bar_chart(r_df, driver_names, title="Driver Points"):
    """
    Horizontal bar — driver abbreviation on y-axis, points on x-axis.
    Clean and readable even with 22 drivers.
    """
    dp = (
        r_df.groupby("driver")["total_points"].sum()
        .reset_index().sort_values("total_points", ascending=True)
    )
    dp["abbr"]  = dp["driver"]
    dp["label"] = dp["driver"].apply(
        lambda d: driver_names.get(d, (d, ""))[0].split()[-1]  # last name only
    )

    fig = go.Figure(go.Bar(
        x=dp["total_points"],
        y=dp["label"],
        orientation="h",
        marker=dict(
            color=dp["total_points"],
            colorscale=[[0, "#2a0000"], [0.5, "#880000"], [1, "#e10600"]],
            showscale=False,
        ),
        text=dp["total_points"].astype(int),
        textposition="outside",
        textfont=dict(size=11, color="#888"),
        hovertemplate="<b>%{y}</b><br>Points: %{x}<extra></extra>",
    ))
    themed(fig, title)
    max_pts = dp["total_points"].max() if not dp.empty else 100
    headroom = max_pts * 1.30 if max_pts > 0 else 100
    fig.update_xaxes(showgrid=True, range=[0, headroom])
    fig.update_yaxes(tickfont=dict(size=11), automargin=True)
    fig.update_layout(
        height=520,
        margin=dict(l=110, r=40, t=44, b=10),
    )
    return fig


def team_bar_chart(r_df, title="Constructor Points", horizontal=True):
    """
    Always horizontal — team on y-axis, points on x-axis.
    Sorted highest to lowest (top of chart = leader).
    """
    tp = (
        r_df.groupby("team")["total_points"].sum()
        .reset_index().sort_values("total_points", ascending=True)
    )

    fig = go.Figure(go.Bar(
        x=tp["total_points"],
        y=tp["team"],
        orientation="h",
        marker=dict(
            color=tp["total_points"],
            colorscale=[[0, "#2a0000"], [0.5, "#880000"], [1, "#e10600"]],
            showscale=False,
        ),
        text=tp["total_points"].astype(int),
        textposition="outside",
        textfont=dict(size=11, color="#888"),
        hovertemplate="<b>%{y}</b><br>Points: %{x}<extra></extra>",
    ))
    themed(fig, title)
    max_pts = tp["total_points"].max() if not tp.empty else 100
    headroom = max_pts * 1.30 if max_pts > 0 else 100
    fig.update_xaxes(showgrid=True, range=[0, headroom])
    fig.update_yaxes(tickfont=dict(size=11), automargin=True)
    fig.update_layout(
        height=380,
        margin=dict(l=130, r=40, t=44, b=10),
    )
    return fig


def win_distribution_pie(r_df, driver_names):
    """
    Donut chart with outside labels — no cramped legacy box.
    """
    wins = r_df[r_df["finish_pos"] == 1]["driver"].value_counts().reset_index()
    wins.columns = ["Driver", "Wins"]
    wins["Name"] = wins["Driver"].apply(
        lambda d: driver_names.get(d, (d, ""))[0].split()[-1]  # last name
    )
    fig = go.Figure(go.Pie(
        labels=wins["Name"],
        values=wins["Wins"],
        hole=0.55,
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=12, color="#aaa"),
        marker=dict(
            colors=RED_SCALE[:len(wins)],
            line=dict(color="#0d0d0d", width=2),
        ),
        hovertemplate="<b>%{label}</b><br>Wins: %{value}<br>%{percent}<extra></extra>",
    ))
    themed(fig, "Win Distribution")
    fig.update_layout(
        height=360,
        showlegend=False,
        margin=dict(l=30, r=30, t=44, b=30),
    )
    return fig


def pole_to_win_gauge(r_df):
    pole = r_df[r_df["grid_pos"] == 1]
    rate = len(pole[pole["finish_pos"] == 1]) / len(pole) * 100 if len(pole) > 0 else 0
    fig  = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(rate, 1),
        number=dict(suffix="%", font=dict(color="#e10600", size=44)),
        title=dict(text="Pole to Win Conversion", font=dict(size=13, color="#666")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#333", tickfont=dict(color="#555", size=10)),
            bar=dict(color="#e10600", thickness=0.7),
            bgcolor="#111",
            bordercolor="#222",
            borderwidth=1,
            steps=[
                dict(range=[0,  50], color="#1a0000"),
                dict(range=[50, 100], color="#330000"),
            ],
            threshold=dict(
                line=dict(color="#fff", width=2),
                thickness=0.8,
                value=round(rate, 1),
            ),
        ),
    ))
    themed(fig)
    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=44, b=20),
    )
    return fig


# ── Driver comparison ────────────────────────────────────────────────────────

def driver_points_progression(r_df, driver_names, drivers):
    sub = r_df[r_df["driver"].isin(drivers)].sort_values("race_id").copy()
    sub["cumpts"] = sub.groupby("driver")["total_points"].cumsum()
    sub["dname"]  = sub["driver"].apply(lambda d: driver_names.get(d, (d, "", ""))[0])
    fig = px.line(
        sub, x="race_id", y="cumpts", color="dname",
        labels={"race_id": "Round", "cumpts": "Points", "dname": "Driver"},
        color_discrete_sequence=["#e10600", "#ff6666"],
    )
    fig.update_traces(line=dict(width=2.5), mode="lines+markers", marker=dict(size=6))
    themed(fig, "Points Progression")
    fig.update_xaxes(tickangle=45, tickfont=dict(size=9))
    fig.update_layout(height=320, legend=dict(orientation="h", y=-0.22))
    return fig


def driver_finish_trend(r_df, driver_names, drivers):
    sub = r_df[r_df["driver"].isin(drivers)].sort_values("race_id").copy()
    sub["dname"] = sub["driver"].apply(lambda d: driver_names.get(d, (d, "", ""))[0])
    fig = px.line(
        sub, x="race_id", y="finish_pos", color="dname",
        labels={"race_id": "Round", "finish_pos": "Finish Pos", "dname": "Driver"},
        color_discrete_sequence=["#e10600", "#ff6666"],
    )
    fig.update_traces(line=dict(width=2), mode="lines+markers", marker=dict(size=6))
    themed(fig, "Finishing Position Trend")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickangle=45, tickfont=dict(size=9))
    fig.update_layout(height=320, legend=dict(orientation="h", y=-0.22))
    return fig


def head_to_head_bar(stats_a, stats_b, drv_a, drv_b, driver_names):
    name_a  = driver_names.get(drv_a, (drv_a, ""))[0].split()[-1]
    name_b  = driver_names.get(drv_b, (drv_b, ""))[0].split()[-1]
    metrics = ["Points", "Wins", "Podiums"]
    vals_a  = [stats_a.get("points", 0), stats_a.get("wins", 0), stats_a.get("podiums", 0)]
    vals_b  = [stats_b.get("points", 0), stats_b.get("wins", 0), stats_b.get("podiums", 0)]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=name_a, x=metrics, y=vals_a,
        marker_color="#e10600",
        text=vals_a, textposition="outside",
        textfont=dict(color="#aaa", size=12),
    ))
    fig.add_trace(go.Bar(
        name=name_b, x=metrics, y=vals_b,
        marker_color="#ff6666",
        text=vals_b, textposition="outside",
        textfont=dict(color="#aaa", size=12),
    ))
    fig.update_layout(
        barmode="group", height=320,
        legend=dict(orientation="h", y=-0.22, font=dict(size=11)),
    )
    themed(fig, "Head-to-Head")
    return fig


# ── Team comparison ──────────────────────────────────────────────────────────

def team_points_progression(r_df, teams):
    sub = r_df[r_df["team"].isin(teams)].sort_values("race_id").copy()
    sub["cumpts"] = sub.groupby("team")["total_points"].cumsum()
    fig = px.line(
        sub, x="race_id", y="cumpts", color="team",
        labels={"race_id": "Round", "cumpts": "Points", "team": "Team"},
        color_discrete_sequence=["#e10600", "#ff6666"],
    )
    fig.update_traces(line=dict(width=2.5), mode="lines+markers", marker=dict(size=6))
    themed(fig, "Team Points Progression")
    fig.update_xaxes(tickangle=45, tickfont=dict(size=9))
    fig.update_layout(height=320, legend=dict(orientation="h", y=-0.22))
    return fig


def driver_contribution_chart(r_df, team, driver_names):
    sub     = r_df[r_df["team"] == team].copy()
    contrib = sub.groupby("driver")["total_points"].sum().reset_index()
    contrib["dname"] = contrib["driver"].apply(
        lambda d: driver_names.get(d, (d, ""))[0].split()[-1]
    )
    fig = go.Figure(go.Pie(
        labels=contrib["dname"],
        values=contrib["total_points"],
        hole=0.5,
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=12, color="#aaa"),
        marker=dict(
            colors=["#e10600", "#ff6666"],
            line=dict(color="#0d0d0d", width=2),
        ),
    ))
    themed(fig, f"{team} — Driver Contribution")
    fig.update_layout(height=300, showlegend=False, margin=dict(l=20, r=20, t=44, b=20))
    return fig


def qualifying_performance_chart(r_df, teams):
    sub = r_df[r_df["team"].isin(teams)].copy()
    avg = sub.groupby("team")["grid_pos"].mean().reset_index().sort_values("grid_pos")
    fig = go.Figure(go.Bar(
        x=avg["team"],
        y=avg["grid_pos"],
        marker_color=["#e10600", "#ff6666"][:len(avg)],
        text=avg["grid_pos"].round(1),
        textposition="outside",
        textfont=dict(color="#aaa", size=12),
    ))
    themed(fig, "Avg Qualifying Position (lower = better)")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=300)
    return fig


def race_pace_chart(r_df, teams):
    sub = r_df[r_df["team"].isin(teams)].copy()
    avg = sub.groupby("team")["finish_pos"].mean().reset_index().sort_values("finish_pos")
    fig = go.Figure(go.Bar(
        x=avg["team"],
        y=avg["finish_pos"],
        marker_color=["#e10600", "#ff6666"][:len(avg)],
        text=avg["finish_pos"].round(1),
        textposition="outside",
        textfont=dict(color="#aaa", size=12),
    ))
    themed(fig, "Avg Finish Position (lower = better)")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=300)
    return fig


# ── Predictions ──────────────────────────────────────────────────────────────

def win_prob_chart(pred_df, driver_names, title="Win Probability (%)"):
    head = pred_df.head(10).copy()
    head["label"] = head["driver"].apply(
        lambda d: driver_names.get(d, (d, ""))[0].split()[-1] + f" ({d})"
    )
    fig = go.Figure(go.Bar(
        x=head["win_probability"] * 100,
        y=head["label"],
        orientation="h",
        marker=dict(
            color=head["win_probability"] * 100,
            colorscale=[[0, "#2a0000"], [0.5, "#880000"], [1, "#e10600"]],
            showscale=False,
        ),
        text=[f"{v:.1f}%" for v in head["win_probability"] * 100],
        textposition="outside",
        textfont=dict(size=11, color="#888"),
        hovertemplate="<b>%{y}</b><br>Win probability: %{x:.1f}%<extra></extra>",
    ))
    themed(fig, title)
    fig.update_yaxes(categoryorder="total ascending", tickfont=dict(size=11), automargin=True)
    fig.update_xaxes(range=[0, 130])
    fig.update_layout(
        height=420,
        margin=dict(l=120, r=40, t=44, b=10),
    )
    return fig


# ── Analytics ────────────────────────────────────────────────────────────────

def lap_time_evolution(l_df, race_id, drivers, driver_names):
    sub = l_df[
        (l_df["race_id"] == race_id) &
        l_df["lap_time_secs"].notna() &
        l_df["driver"].isin(drivers)
    ].copy()
    sub["dname"] = sub["driver"].apply(lambda d: driver_names.get(d, (d, "", ""))[0].split()[-1])
    fig = px.line(
        sub, x="lap_number", y="lap_time_secs", color="dname",
        labels={"lap_number": "Lap", "lap_time_secs": "Lap Time (s)", "dname": "Driver"},
        color_discrete_sequence=RED_SCALE,
    )
    themed(fig, "Lap Time Evolution")
    fig.update_layout(height=340, legend=dict(orientation="h", y=-0.22, font=dict(size=10)))
    return fig


def tyre_degradation_chart(l_df, race_id, drivers):
    sub = (
        l_df[
            (l_df["race_id"] == race_id) &
            l_df["lap_time_secs"].notna() &
            l_df["driver"].isin(drivers)
        ]
        .groupby(["tyre_compound", "tyre_age"])["lap_time_secs"]
        .mean().reset_index()
    )
    if sub.empty:
        return None
    fig = px.line(
        sub, x="tyre_age", y="lap_time_secs", color="tyre_compound",
        labels={"tyre_age": "Tyre Age (laps)", "lap_time_secs": "Avg Lap Time (s)"},
        color_discrete_map=TYRE_COLORS,
    )
    themed(fig, "Tyre Degradation")
    fig.update_layout(height=340, legend=dict(orientation="h", y=-0.22, font=dict(size=10)))
    return fig


def tyre_usage_chart(l_df, race_id, drivers):
    sub = (
        l_df[(l_df["race_id"] == race_id) & l_df["driver"].isin(drivers)]
        .groupby(["driver", "tyre_compound"]).size().reset_index(name="laps")
    )
    if sub.empty:
        return None
    fig = px.bar(
        sub, x="driver", y="laps", color="tyre_compound",
        color_discrete_map=TYRE_COLORS,
    )
    themed(fig, "Tyre Strategy")
    fig.update_xaxes(tickangle=45, tickfont=dict(size=10))
    fig.update_layout(height=340, legend=dict(orientation="h", y=-0.28, font=dict(size=10)))
    return fig


def position_changes_chart(r_df, race_id):
    sub = r_df[r_df["race_id"] == race_id].copy()
    if sub.empty or "grid_pos" not in sub.columns:
        return None
    fig = go.Figure()
    colors = RED_SCALE * 3
    for idx, (_, row) in enumerate(sub.iterrows()):
        gain  = (row["grid_pos"] or 0) - (row["finish_pos"] or 0)
        color = "#22c55e" if gain > 0 else ("#e10600" if gain < 0 else "#666")
        fig.add_trace(go.Scatter(
            x=["Grid", "Finish"],
            y=[row["grid_pos"], row["finish_pos"]],
            mode="lines+markers+text",
            name=row["driver"],
            text=[row["driver"], ""],
            textposition="middle left",
            textfont=dict(size=10, color="#888"),
            line=dict(color=color, width=1.5),
            marker=dict(size=7, color=color),
            showlegend=False,
        ))
    themed(fig, "Grid → Finish Position Changes")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=420)
    return fig


def qualifying_vs_race_scatter(r_df, race_id):
    sub = r_df[r_df["race_id"] == race_id].copy()
    if sub.empty:
        return None
    fig = px.scatter(
        sub, x="grid_pos", y="finish_pos",
        color="driver", text="driver",
        labels={"grid_pos": "Grid", "finish_pos": "Finish", "driver": "Driver"},
        color_discrete_sequence=RED_SCALE,
        opacity=0.85,
    )
    fig.update_traces(textposition="top center", marker=dict(size=10))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(autorange="reversed")
    themed(fig, "Grid vs Finish Position")
    fig.update_layout(height=340, showlegend=False)
    return fig


def race_pace_analysis(l_df, race_id, drivers, driver_names):
    sub = l_df[
        (l_df["race_id"] == race_id) &
        l_df["lap_time_secs"].notna() &
        l_df["driver"].isin(drivers)
    ].copy()
    if sub.empty:
        return None
    sub["dname"] = sub["driver"].apply(
        lambda d: driver_names.get(d, (d, "", ""))[0].split()[-1]
    )
    fig = px.box(
        sub, x="dname", y="lap_time_secs",
        labels={"dname": "Driver", "lap_time_secs": "Lap Time (s)"},
        color_discrete_sequence=["#e10600"],
    )
    themed(fig, "Race Pace Distribution")
    fig.update_xaxes(tickangle=45, tickfont=dict(size=10))
    fig.update_layout(height=340)
    return fig
