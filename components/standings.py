from utils.helpers import render_html_block, esc


def render_driver_standings(r_df, driver_names, next_name="",
                             show_pred_bar=False, pred_df=None, limit=None):
    pts_df  = r_df.groupby("driver")["total_points"].sum().reset_index()
    wins_df = r_df[r_df["finish_pos"] == 1].groupby("driver").size().reset_index(name="wins")
    pod_df  = r_df[r_df["finish_pos"] <= 3].groupby("driver").size().reset_index(name="podiums")
    team_df = (
        r_df.sort_values("race_id").groupby("driver").last()
        .reset_index()[["driver", "team"]]
    )
    standings = (
        pts_df.merge(wins_df, on="driver", how="left")
              .merge(pod_df,  on="driver", how="left")
              .merge(team_df, on="driver", how="left")
              .fillna(0)
              .sort_values("total_points", ascending=False)
              .reset_index(drop=True)
    )
    if limit:
        standings = standings.head(limit)

    prev_race_ids = sorted(r_df["race_id"].unique())
    prev_pts = {}
    if len(prev_race_ids) >= 2:
        prev_pts = (
            r_df[r_df["race_id"] == prev_race_ids[-2]]
            .set_index("driver")["total_points"].to_dict()
        )

    pos_colors = ["#e10600", "#ff3333", "#cc0000"] + ["#555"] * 30
    parts = []
    for i, row in standings.iterrows():
        drv   = row["driver"]
        name  = esc(driver_names.get(drv, (drv, "", "#e10600"))[0])
        team  = esc(row["team"])
        pts   = int(row["total_points"])
        wins  = int(row["wins"])
        pods  = int(row["podiums"])
        delta = pts - int(prev_pts.get(drv, pts))
        delta_html = (
            f'<span class="p2p-pts-delta"> ▲{delta}</span>'
            if delta > 0 else ""
        )

        pred_html = ""
        if show_pred_bar and pred_df is not None and not pred_df.empty:
            pr = pred_df[pred_df["driver"] == drv]
            if not pr.empty:
                prob = pr.iloc[0]["win_probability"] * 100
                pred_html = (
                    f'<div class="p2p-prob-track">'
                    f'<div class="p2p-prob-fill" style="width:{min(prob,100):.0f}%;"></div>'
                    f'</div>'
                    f'<div class="p2p-prob-lbl">'
                    f'{prob:.0f}% win prob — {esc(next_name)}</div>'
                )

        podium = ["podium-1", "podium-2", "podium-3"][i] if i < 3 else ""
        parts.append(
            f'<div class="p2p-driver-row {podium}">'
            f'  <div class="p2p-driver-pos" style="color:{pos_colors[i]};">{i + 1}</div>'
            f'  <div class="p2p-driver-badge">{esc(drv)}</div>'
            f'  <div class="p2p-driver-info">'
            f'    <div class="p2p-driver-fullname">{name}</div>'
            f'    <div class="p2p-driver-meta">'
            f'      <span style="color:#e10600;font-size:0.65rem;">●</span>'
            f'      <span>{team}</span>'
            f'      <span class="p2p-driver-abbr">{esc(drv)}</span>'
            f'    </div>{pred_html}'
            f'  </div>'
            f'  <div class="p2p-driver-stats">'
            f'    <div class="p2p-stat">'
            f'      <div class="p2p-stat-val">{wins}</div>'
            f'      <div class="p2p-stat-label">Wins</div>'
            f'    </div>'
            f'    <div class="p2p-stat">'
            f'      <div class="p2p-stat-val">{pods}</div>'
            f'      <div class="p2p-stat-label">Pods</div>'
            f'    </div>'
            f'  </div>'
            f'  <div class="p2p-pts-block">'
            f'    <div class="p2p-pts-val">{pts}</div>'
            f'    <div class="p2p-pts-label">PTS{delta_html}</div>'
            f'  </div>'
            f'</div>'
        )
    render_html_block("".join(parts))


def render_team_standings(r_df, limit=None):
    tp = (
        r_df.groupby("team")["total_points"].sum()
        .reset_index()
        .sort_values("total_points", ascending=False)
    )
    if limit:
        tp = tp.head(limit)

    prev_race_ids = sorted(r_df["race_id"].unique())
    prev_pts = {}
    if len(prev_race_ids) >= 2:
        prev_pts = (
            r_df[r_df["race_id"] == prev_race_ids[-2]]
            .groupby("team")["total_points"].sum().to_dict()
        )

    rows  = tp.values.tolist()
    parts = []
    rank  = 0
    for i in range(0, len(rows), 2):
        parts.append('<div class="p2p-team-grid">')
        for j in range(2):
            if i + j < len(rows):
                rank += 1
                team, pts = rows[i + j][0], int(rows[i + j][1])
                delta  = pts - int(prev_pts.get(team, pts))
                d_html = (
                    f'<div class="p2p-team-delta">▲ {delta} pts this round</div>'
                    if delta > 0 else ""
                )
                abbr = esc("".join(w[0] for w in team.split()[:2]).upper())
                parts.append(
                    f'<div class="p2p-team-card"><div>'
                    f'  <div class="p2p-team-rank">P{rank}</div>'
                    f'  <div class="p2p-team-name">{esc(team)}</div>'
                    f'  <div class="p2p-team-pts">{pts} <small>PTS</small></div>'
                    f'  {d_html}'
                    f'</div>'
                    f'<div class="p2p-team-badge">{abbr}</div>'
                    f'</div>'
                )
        parts.append("</div>")
    render_html_block("".join(parts))


def render_pred_list(pred_df, max_rows=15):
    max_prob = pred_df["win_probability"].max()
    parts = ['<div class="pred-list">']
    for _, row in pred_df.head(max_rows).iterrows():
        prob  = row["win_probability"] * 100
        width = (row["win_probability"] / max_prob) * 100 if max_prob > 0 else 0
        parts.append(
            f'<div class="pred-row">'
            f'  <div class="pred-pos">P{int(row["grid_pos"])}</div>'
            f'  <div class="pred-drv">{esc(row["driver"])}</div>'
            f'  <div class="pred-team">{esc(row["team"])}</div>'
            f'  <div class="pred-bar-bg">'
            f'    <div class="pred-bar" style="width:{width:.0f}%;"></div>'
            f'  </div>'
            f'  <div class="pred-pct">{prob:.1f}%</div>'
            f'</div>'
        )
    parts.append("</div>")
    render_html_block("".join(parts))