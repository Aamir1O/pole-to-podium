import streamlit as st
from utils.helpers import render_html_block, esc


def render_hero_stats(r_df, driver_names):
    if r_df.empty:
        return
    races       = r_df["race_id"].nunique()
    leader_drv  = r_df.groupby("driver")["total_points"].sum().idxmax()
    leader_pts  = int(r_df.groupby("driver")["total_points"].sum().max())
    leader_name = driver_names.get(leader_drv, (leader_drv, ""))[0]
    leader_team = r_df[r_df["driver"] == leader_drv]["team"].iloc[-1]
    wins        = int((r_df["finish_pos"] == 1).sum())
    render_html_block(
        f'<div class="p2p-hero fade-up">'
        f'<div class="p2p-hero-stat">'
        f'  <div class="p2p-hero-val">{races}</div>'
        f'  <div class="p2p-hero-lbl">Races Complete</div>'
        f'</div>'
        f'<div class="p2p-hero-stat">'
        f'  <div class="p2p-hero-val">{esc(leader_name)}</div>'
        f'  <div class="p2p-hero-lbl">Championship Leader</div>'
        f'</div>'
        f'<div class="p2p-hero-stat">'
        f'  <div class="p2p-hero-val">{leader_pts}<span> PTS</span></div>'
        f'  <div class="p2p-hero-lbl">{esc(leader_team)}</div>'
        f'</div>'
        f'<div class="p2p-hero-stat">'
        f'  <div class="p2p-hero-val">{wins}</div>'
        f'  <div class="p2p-hero-lbl">Race Wins</div>'
        f'</div>'
        f'</div>'
    )


def render_metric_card(label: str, value: str, delta: str = "") -> str:
    delta_html = f'<div class="p2p-metric-delta">{esc(delta)}</div>' if delta else ""
    return (
        f'<div class="p2p-metric-card">'
        f'<div class="p2p-metric-label">{esc(label)}</div>'
        f'<div class="p2p-metric-value">{esc(value)}</div>'
        f'{delta_html}</div>'
    )


def render_race_cards(r_df, driver_names, limit: int = 8) -> None:
    races = (
        r_df[["race_id", "race_name", "circuit", "date"]]
        .drop_duplicates()
        .sort_values("race_id", ascending=False)
        .head(limit)
    )
    parts = []
    for _, race in races.iterrows():
        wr = r_df[(r_df["race_id"] == race["race_id"]) & (r_df["finish_pos"] == 1)]
        if not wr.empty:
            drv    = wr.iloc[0]["driver"]
            wname  = esc(driver_names.get(drv, (drv, "", ""))[0])
            winner = f'<div class="p2p-race-winner">Winner: {wname}</div>'
            badge  = '<span class="p2p-race-badge">Finished</span>'
        else:
            winner = (
                '<div style="font-size:0.72rem;color:#e10600;'
                'font-weight:600;margin-top:0.15rem;">Race in progress</div>'
            )
            badge = '<span class="p2p-race-badge upcoming">Live</span>'
        date_str = esc(str(race["date"])[:10] if race["date"] else "")
        parts.append(
            f'<div class="p2p-race-card"><div>'
            f'<div class="p2p-race-name">{esc(race["race_name"])}</div>'
            f'<div class="p2p-race-sub">{date_str} · {esc(race["circuit"])}</div>'
            f'{winner}</div>{badge}</div>'
        )
    render_html_block("".join(parts))


def render_comparison_stats(stats_a: dict, stats_b: dict) -> None:
    metrics = [
        ("Points",     "points"),
        ("Wins",       "wins"),
        ("Podiums",    "podiums"),
        ("Avg Finish", "avg_finish"),
        ("Avg Grid",   "avg_grid"),
    ]
    parts = ['<div class="p2p-cmp-grid">']
    for label, key in metrics:
        va = stats_a.get(key, "—")
        vb = stats_b.get(key, "—")
        if isinstance(va, float):
            va = f"{va:.1f}"
        if isinstance(vb, float):
            vb = f"{vb:.1f}"
        parts.append(
            f'<div class="p2p-cmp-card">'
            f'<div class="p2p-cmp-label">{esc(label)}</div>'
            f'<div class="p2p-cmp-val-a">{esc(str(va))}</div>'
            f'<div class="p2p-cmp-vs">vs</div>'
            f'<div class="p2p-cmp-val-b">{esc(str(vb))}</div>'
            f'</div>'
        )
    parts.append("</div>")
    render_html_block("".join(parts))