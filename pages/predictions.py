import streamlit as st
from utils.helpers import page_head, section, show_chart, render_html_block, esc
from components.standings import render_pred_list
from components.charts import win_prob_chart


def render(r_df, q_df, l_df, w_df, results_all, laps_all,
           driver_names, next_name, next_circuit,
           pred_fn, le_driver, le_team, le_circuit, features, model):

    page_head("Race Predictions", "Race Weekend Intelligence Center")

    latest_race_id = q_df["race_id"].max() if not q_df.empty else None

    if not latest_race_id:
        st.markdown(
            '<div style="color:#444;font-size:0.9rem;padding:3rem 0;text-align:center;">'
            'No qualifying data found. Predictions will appear once '
            'qualifying data is loaded.</div>',
            unsafe_allow_html=True,
        )
        return

    ri   = r_df[r_df["race_id"] == latest_race_id]
    circ = ri["circuit"].iloc[0] if not ri.empty else next_circuit

    try:
        pred = pred_fn(
            results_all, laps_all, q_df, w_df,
            latest_race_id, circ,
            le_driver=le_driver, le_team=le_team,
            le_circuit=le_circuit, features=features, model=model,
        )
    except Exception:
        pred = None

    # ── Notice ────────────────────────────────────────────────────────────────
    render_html_block(
        f'<div class="p2p-notice">'
        f'<span class="notice-icon">🏁</span>'
        f'<span>Analysing: <strong>{esc(latest_race_id)}</strong> — {esc(circ)}. '
        f'Probabilities are generated from qualifying session data using an '
        f'XGBoost model trained on historical race outcomes.</span>'
        f'</div>'
    )

    if pred is None or pred.empty:
        st.markdown(
            '<div style="color:#444;font-size:0.85rem;padding:2rem 0;text-align:center;">'
            'Qualifying data not yet available for this race weekend.</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Top 3 prediction cards ────────────────────────────────────────────────
    section("Top 3", "Predicted Finishers")

    medals    = ["🥇", "🥈", "🥉"]
    pos_cls   = ["p1", "p2", "p3"]
    pos_label = ["P1 PREDICTED", "P2 PREDICTED", "P3 PREDICTED"]

    c1, c2, c3 = st.columns(3)
    for i, col in enumerate([c1, c2, c3]):
        if i < len(pred):
            row  = pred.iloc[i]
            drv  = row["driver"]
            name = driver_names.get(drv, (drv, "", ""))[0]
            team = row["team"]
            prob = row["win_probability"] * 100
            col.markdown(
                f'<div class="p2p-pred-card {pos_cls[i]}">'
                f'<div class="p2p-pred-medal">{medals[i]}</div>'
                f'<div class="p2p-pred-pos">{pos_label[i]}</div>'
                f'<div class="p2p-pred-name">{esc(name)}</div>'
                f'<div class="p2p-pred-team">{esc(team)}</div>'
                f'<div class="p2p-pred-prob">{prob:.1f}%</div>'
                f'<div class="p2p-pred-prob-lbl">Win Probability</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Win probability chart — hero ──────────────────────────────────────────
    section("Win Probability", "Distribution")
    fig = win_prob_chart(
        pred, driver_names,
        title=f"Win Probability — {latest_race_id}",
    )
    fig.update_layout(height=460)
    show_chart(fig)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Prediction table + model insights ─────────────────────────────────────
    col_tbl, col_info = st.columns([1.6, 1])

    with col_tbl:
        section("Full", "Prediction Table")
        render_pred_list(pred, max_rows=20)

    with col_info:
        section("Model", "Insights")

        render_html_block(
            '<div class="p2p-metric-card">'
            '<div class="p2p-metric-label">Model Type</div>'
            '<div class="p2p-metric-value">XGBoost Classifier</div>'
            '</div>'
        )
        st.markdown("<br>", unsafe_allow_html=True)

        render_html_block(
            '<div class="p2p-metric-card">'
            '<div class="p2p-metric-label">Training Data</div>'
            '<div class="p2p-metric-value">Historical Race Outcomes</div>'
            '</div>'
        )
        st.markdown("<br>", unsafe_allow_html=True)

        render_html_block(
            '<div class="p2p-metric-card">'
            '<div class="p2p-metric-label">Key Features</div>'
            '<div class="p2p-metric-value">'
            'Grid pos · Quali time · Win rate · Weather · Tyre'
            '</div>'
            '</div>'
        )
        st.markdown("<br>", unsafe_allow_html=True)

        render_html_block(
            '<div class="p2p-notice">'
            '<span class="notice-icon">◎</span>'
            '<span>Probabilities update after each qualifying session. '
            'Model accuracy improves as more race data is added.</span>'
            '</div>'
        )