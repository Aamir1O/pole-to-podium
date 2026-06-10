import streamlit as st

CSS = """
    :root {
        --bg: #030303;
        --surface: rgba(14,14,14,0.92);
        --surface2: rgba(20,20,20,0.95);
        --border: rgba(255,255,255,0.06);
        --border-hot: rgba(225,6,0,0.45);
        --red: #e10600;
        --red-bright: #ff2a2a;
        --red-dim: #8b0000;
        --text: #f2f2f2;
        --muted: #6b6b6b;
        --glow: 0 0 28px rgba(225,6,0,0.22);
        --radius: 14px;
        --font: 'Outfit', system-ui, sans-serif;
        --mono: 'JetBrains Mono', monospace;
    }

    body, html, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMainViewContainer"] {
        background: var(--bg) !important;
        color: var(--text) !important;
        font-family: var(--font) !important;
    }

    .stApp::before {
        content: '';
        position: fixed; inset: 0; z-index: 0; pointer-events: none;
        background:
            radial-gradient(ellipse 80% 50% at 15% -10%, rgba(225,6,0,0.14) 0%, transparent 55%),
            radial-gradient(ellipse 60% 40% at 90% 5%,  rgba(225,6,0,0.08) 0%, transparent 50%),
            radial-gradient(ellipse 50% 30% at 50% 100%,rgba(225,6,0,0.05) 0%, transparent 60%);
    }

    [data-testid="stHeader"],
    [data-testid="stFooter"],
    [data-testid="stDecoration"] { display:none !important; }
    section[data-testid="stSidebar"] { display:none !important; }
    [data-testid="stMainBlockContainer"] { padding-top:0 !important; position:relative; z-index:1; }
    .block-container { padding: 0 2.2rem 3rem 2.2rem !important; max-width:1400px !important; margin:0 auto !important; }
    #MainMenu, footer, header { visibility:hidden !important; }

    ::-webkit-scrollbar { width:6px; height:6px; }
    ::-webkit-scrollbar-track { background:var(--bg); }
    ::-webkit-scrollbar-thumb { background:#2a2a2a; border-radius:99px; }
    ::-webkit-scrollbar-thumb:hover { background:var(--red); }

    @keyframes fadeUp {
        from { opacity:0; transform:translateY(14px); }
        to   { opacity:1; transform:translateY(0); }
    }
    @keyframes glowPulse {
        0%,100% { box-shadow:0 0 12px rgba(225,6,0,0.35); }
        50%      { box-shadow:0 0 22px rgba(225,6,0,0.65); }
    }
    .fade-up { animation: fadeUp 0.55s ease both; }

    /* ── Navbar ─────────────────────────────────── */
    .p2p-navbar {
        display:flex; align-items:center; height:62px;
        background: rgba(3,3,3,0.95); backdrop-filter: blur(20px);
        border-bottom:1px solid var(--border);
        padding:0 2.2rem;
        margin:0 -2.2rem 0 -2.2rem;
        position:sticky; top:0; z-index:100;
    }
    .p2p-navbar::after {
        content:''; position:absolute; bottom:0; left:0; right:0; height:1px;
        background: linear-gradient(90deg, transparent, var(--red), transparent);
        opacity:0.5;
    }
    .p2p-logo {
        display:flex; align-items:center; gap:0.55rem;
        font-size:1.1rem; font-weight:900; letter-spacing:-0.03em;
        margin-right:1.4rem; flex-shrink:0;
    }
    .p2p-logo .logo-icon {
        width:38px; height:26px; border-radius:6px;
        background: #0a0a0a; border:1px solid var(--border-hot);
        display:flex; align-items:center; justify-content:center;
        animation: glowPulse 3s ease infinite;
        box-shadow: var(--glow); padding:2px 4px;
    }
    .f1-logo-svg { width:30px; height:14px; display:block; }
    .p2p-logo .logo-text  { color:#fff; }
    .p2p-logo .logo-accent{ color:var(--red); }
    .p2p-nav-divider {
        width:1px; height:26px; background:var(--border);
        margin:0 1rem; flex-shrink:0;
    }
    .p2p-next-race {
        display:flex; align-items:center; gap:0.5rem;
        background: var(--surface); border:1px solid var(--border);
        border-radius:999px; padding:0.3rem 0.9rem 0.3rem 0.75rem;
        flex-shrink:0;
    }
    .p2p-next-race .nr-flag {
        font-family:var(--mono); font-size:0.58rem; text-transform:uppercase;
        letter-spacing:0.12em; color:var(--muted); font-weight:600;
    }
    .p2p-next-race .nr-name { font-size:0.78rem; font-weight:700; color:#fff; }

    div[data-testid="stRadio"] { display:none !important; }

    .p2p-nav-links {
        display:flex; align-items:stretch; margin-left:auto; height:100%;
    }
    .p2p-nav-link {
        display:flex; align-items:center; gap:0.42rem; padding:0 0.95rem;
        font-size:0.78rem; font-weight:600; color:var(--muted);
        border:none; background:transparent; cursor:pointer;
        position:relative; transition:color 0.2s ease;
        font-family:var(--font); white-space:nowrap; letter-spacing:0.02em;
    }
    .p2p-nav-link:hover { color:#ccc; }
    .p2p-nav-link.active { color:#fff; }
    .p2p-nav-link.active::after {
        content:''; position:absolute; bottom:0; left:0.6rem; right:0.6rem; height:2px;
        background:var(--red); border-radius:2px 2px 0 0;
    }
    .p2p-nav-link svg { opacity:0.55; flex-shrink:0; }
    .p2p-nav-link.active svg { opacity:1; }

    button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {
        background: transparent !important;
        border: 1px solid var(--border) !important;
        color: var(--muted) !important;
        border-radius: 999px !important;
        font-family: var(--font) !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }
    button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover {
        border-color: rgba(255,255,255,0.12) !important;
        color: #ccc !important;
        background: transparent !important;
    }

    button[kind="tertiary"],
    button[data-testid="baseButton-tertiary"] {
        background: transparent !important;
        border: none !important;
        color: var(--red) !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        padding: 0 !important;
        min-height: unset !important;
        box-shadow: none !important;
        line-height: 1 !important;
    }
    button[kind="tertiary"]:hover,
    button[data-testid="baseButton-tertiary"]:hover {
        color: var(--red-bright) !important;
        text-decoration: underline !important;
        background: transparent !important;
    }

    div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 0.5rem !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
        display: flex !important;
        align-items: center !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child > div {
        justify-content: flex-start !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child > div {
        justify-content: flex-end !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child button {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        height: auto !important;
        min-height: unset !important;
    }
    div[data-testid="stHorizontalBlock"] .p2p-section-title {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }

    /* ── Page head ───────────────────────────────── */
    .p2p-page-head { margin-bottom:1.4rem; padding-top:0.8rem; }
    .p2p-page-title {
        font-size:2.2rem; font-weight:900; letter-spacing:-0.04em; line-height:1.1;
        margin-bottom:0.3rem;
        background: linear-gradient(135deg, #fff 40%, #888 100%);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        background-clip:text;
    }
    .p2p-page-sub { font-size:0.85rem; color:var(--muted); font-weight:500; }

    /* ── Hero stats ──────────────────────────────── */
    .p2p-hero {
        display:grid; grid-template-columns:repeat(4,1fr); gap:0.75rem;
        margin-bottom:1.6rem; padding:1.1rem;
        background: var(--surface); border:1px solid var(--border);
        border-radius: var(--radius); position:relative; overflow:hidden;
    }
    .p2p-hero::before {
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background: linear-gradient(90deg, transparent, var(--red), transparent);
    }
    .p2p-hero-stat { text-align:center; padding:0.5rem 0.25rem; }
    .p2p-hero-val {
        font-size:1.75rem; font-weight:900; color:#fff;
        letter-spacing:-0.03em; line-height:1;
    }
    .p2p-hero-val span { font-size:0.9rem; color:var(--red); font-weight:700; }
    .p2p-hero-lbl {
        font-family:var(--mono); font-size:0.62rem; text-transform:uppercase;
        letter-spacing:0.14em; color:var(--muted); margin-top:0.35rem; font-weight:600;
    }

    /* ── Section title ───────────────────────────── */
    .p2p-section-title {
        font-size:0.72rem; font-weight:700; color:var(--muted);
        margin:1.4rem 0 0.85rem; text-transform:uppercase; letter-spacing:0.16em;
        display:flex; align-items:center; gap:0.6rem;
    }
    .p2p-section-title::before {
        content:''; width:3px; height:14px; background:var(--red);
        border-radius:2px; box-shadow:0 0 8px rgba(225,6,0,0.6);
    }
    .p2p-section-title span { color:var(--red); letter-spacing:0.12em; }

    /* ── Chart hero wrapper ──────────────────────── */
    .p2p-chart-hero {
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius); padding:1rem 1.1rem 0.4rem;
        margin-bottom:1.6rem; position:relative; overflow:hidden;
    }
    .p2p-chart-hero::before {
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background: linear-gradient(90deg, transparent, var(--red), transparent);
    }
    .p2p-chart-hero-title {
        font-size:0.72rem; font-weight:700; color:var(--muted);
        text-transform:uppercase; letter-spacing:0.16em;
        display:flex; align-items:center; gap:0.6rem; margin-bottom:0.6rem;
    }
    .p2p-chart-hero-title::before {
        content:''; width:3px; height:14px; background:var(--red);
        border-radius:2px; box-shadow:0 0 8px rgba(225,6,0,0.6);
    }
    .p2p-chart-hero-title span { color:var(--red); }

    /* ── Team cards ──────────────────────────────── */
    .p2p-team-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.65rem; margin-bottom:0.65rem; }
    .p2p-team-card {
        background:var(--surface2); border:1px solid var(--border);
        border-radius:12px; padding:1.1rem 1.2rem;
        display:flex; align-items:center; justify-content:space-between;
        transition: all 0.25s ease; position:relative; overflow:hidden;
    }
    .p2p-team-card::before {
        content:''; position:absolute; inset:0;
        background: linear-gradient(135deg, rgba(225,6,0,0.06), transparent 60%);
        opacity:0; transition:opacity 0.25s;
    }
    .p2p-team-card:hover { border-color:var(--border-hot); transform:translateY(-2px); box-shadow:var(--glow); }
    .p2p-team-card:hover::before { opacity:1; }
    .p2p-team-rank {
        font-family:var(--mono); font-size:0.65rem; color:var(--red);
        font-weight:700; margin-bottom:0.25rem; letter-spacing:0.08em;
    }
    .p2p-team-name {
        font-size:0.72rem; color:var(--muted); font-weight:600;
        text-transform:uppercase; letter-spacing:0.07em; margin-bottom:0.15rem;
    }
    .p2p-team-pts { font-size:1.55rem; font-weight:900; color:#fff; letter-spacing:-0.03em; }
    .p2p-team-pts small { font-size:0.75rem; font-weight:600; color:var(--muted); }
    .p2p-team-delta { font-size:0.72rem; font-weight:700; color:var(--red); margin-top:0.2rem; }
    .p2p-team-badge {
        width:40px; height:40px; border-radius:10px;
        display:flex; align-items:center; justify-content:center;
        font-family:var(--mono); font-size:0.58rem; font-weight:800;
        color:var(--red); background:rgba(225,6,0,0.1); border:1px solid var(--border-hot);
    }

    /* ── Driver rows ─────────────────────────────── */
    .p2p-driver-row {
        background:var(--surface2); border:1px solid var(--border);
        border-radius:12px; padding:0.9rem 1.15rem; margin-bottom:0.45rem;
        display:flex; align-items:center; gap:0.9rem;
        transition: all 0.22s ease;
    }
    .p2p-driver-row:hover {
        border-color:var(--border-hot); transform:translateX(3px);
        box-shadow:-3px 0 0 var(--red), var(--glow);
    }
    .p2p-driver-row.podium-1 {
        border-left:3px solid var(--red-bright) !important;
        background:linear-gradient(90deg,rgba(225,6,0,0.08),var(--surface2));
    }
    .p2p-driver-row.podium-2 { border-left:3px solid #cc2222 !important; }
    .p2p-driver-row.podium-3 { border-left:3px solid #992222 !important; }
    .p2p-driver-pos {
        font-family:var(--mono); font-size:1.25rem; font-weight:800;
        min-width:28px; text-align:center;
    }
    .p2p-driver-badge {
        min-width:40px; height:40px; border-radius:10px;
        display:flex; align-items:center; justify-content:center;
        font-family:var(--mono); font-size:0.68rem; font-weight:800;
        color:var(--red); background:rgba(225,6,0,0.1); border:1px solid var(--border-hot);
    }
    .p2p-driver-info { flex:1; min-width:0; }
    .p2p-driver-fullname { font-size:0.92rem; font-weight:700; color:#fff; margin-bottom:0.12rem; }
    .p2p-driver-meta { display:flex; align-items:center; gap:0.35rem; font-size:0.7rem; color:var(--muted); }
    .p2p-driver-abbr {
        font-family:var(--mono); background:rgba(255,255,255,0.05);
        border-radius:4px; padding:0.06rem 0.35rem; font-size:0.62rem;
        color:#888; font-weight:700; letter-spacing:0.05em;
    }
    .p2p-prob-track { margin-top:0.35rem; background:rgba(255,255,255,0.05); border-radius:99px; height:4px; overflow:hidden; }
    .p2p-prob-fill  { height:100%; border-radius:99px; background:linear-gradient(90deg,var(--red-dim),var(--red-bright)); }
    .p2p-prob-lbl   { font-family:var(--mono); font-size:0.58rem; color:var(--red); margin-top:0.15rem; font-weight:600; }
    .p2p-driver-stats { display:flex; gap:1.4rem; }
    .p2p-stat { text-align:center; }
    .p2p-stat-val   { font-size:0.9rem; font-weight:800; color:#fff; }
    .p2p-stat-label { font-family:var(--mono); font-size:0.55rem; color:#444; text-transform:uppercase; letter-spacing:0.08em; }
    .p2p-pts-block  { text-align:right; min-width:68px; }
    .p2p-pts-val    { font-size:1.45rem; font-weight:900; color:#fff; letter-spacing:-0.03em; }
    .p2p-pts-label  { font-family:var(--mono); font-size:0.55rem; color:#444; text-transform:uppercase; letter-spacing:0.1em; }
    .p2p-pts-delta  { font-size:0.68rem; font-weight:700; color:var(--red); }

    /* ── Race cards ──────────────────────────────── */
    .p2p-race-card {
        background:var(--surface2); border:1px solid var(--border);
        border-radius:11px; padding:0.9rem 1.1rem; margin-bottom:0.45rem;
        display:flex; align-items:center; justify-content:space-between;
        transition: all 0.22s ease;
    }
    .p2p-race-card:hover { border-color:var(--border-hot); background:rgba(225,6,0,0.04); }
    .p2p-race-name   { font-size:0.86rem; font-weight:700; color:#fff; }
    .p2p-race-sub    { font-size:0.68rem; color:var(--muted); margin-top:0.1rem; }
    .p2p-race-winner { font-size:0.7rem; color:var(--red); font-weight:600; margin-top:0.2rem; }
    .p2p-race-badge  {
        font-family:var(--mono); font-size:0.58rem; font-weight:700;
        text-transform:uppercase; letter-spacing:0.1em;
        padding:0.22rem 0.6rem; border-radius:999px;
        border:1px solid var(--border); color:var(--muted);
    }
    .p2p-race-badge.upcoming { border-color:var(--border-hot); color:var(--red); background:rgba(225,6,0,0.08); }

    /* ── Metric card ─────────────────────────────── */
    .p2p-metric-card {
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius); padding:1.2rem 1.3rem;
        position:relative; overflow:hidden;
    }
    .p2p-metric-card::after {
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg,var(--red-dim),var(--red-bright),var(--red-dim));
    }
    .p2p-metric-label { font-family:var(--mono); font-size:0.62rem; text-transform:uppercase; letter-spacing:0.12em; color:var(--muted); margin-bottom:0.4rem; }
    .p2p-metric-value { font-size:1.1rem; font-weight:800; color:#fff; }
    .p2p-metric-delta { font-size:0.82rem; font-weight:700; color:var(--red); margin-top:0.2rem; }

    /* ── Prediction cards ────────────────────────── */
    .p2p-pred-card {
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius); padding:1.4rem 1.5rem;
        position:relative; overflow:hidden; text-align:center;
        transition: all 0.25s ease;
    }
    .p2p-pred-card:hover { border-color:var(--border-hot); box-shadow:var(--glow); transform:translateY(-2px); }
    .p2p-pred-card.p1 { border-top:3px solid var(--red-bright); }
    .p2p-pred-card.p2 { border-top:3px solid #cc2222; }
    .p2p-pred-card.p3 { border-top:3px solid #992222; }
    .p2p-pred-medal    { font-size:1.6rem; margin-bottom:0.4rem; }
    .p2p-pred-pos      { font-family:var(--mono); font-size:0.65rem; color:var(--red); font-weight:700; letter-spacing:0.1em; margin-bottom:0.3rem; }
    .p2p-pred-name     { font-size:1rem; font-weight:800; color:#fff; margin-bottom:0.15rem; }
    .p2p-pred-team     { font-size:0.7rem; color:var(--muted); margin-bottom:0.5rem; }
    .p2p-pred-prob     { font-size:1.4rem; font-weight:900; color:var(--red); letter-spacing:-0.02em; }
    .p2p-pred-prob-lbl { font-family:var(--mono); font-size:0.58rem; color:#444; text-transform:uppercase; letter-spacing:0.1em; }

    /* ── Notice box ──────────────────────────────── */
    .p2p-notice {
        background:var(--surface); border:1px solid var(--border);
        border-left:3px solid var(--red); border-radius:10px;
        padding:0.85rem 1rem; margin-bottom:1.2rem;
        font-size:0.78rem; color:var(--muted); line-height:1.55;
        display:flex; gap:0.6rem;
    }
    .p2p-notice .notice-icon { color:var(--red); flex-shrink:0; }

    /* ── Pred list ───────────────────────────────── */
    .pred-list { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:0.85rem 1.1rem; }
    .pred-row  { display:flex; align-items:center; gap:0.75rem; padding:0.5rem 0; border-bottom:1px solid rgba(255,255,255,0.04); }
    .pred-row:last-child { border-bottom:none; }
    .pred-pos  { font-family:var(--mono); min-width:22px; font-size:0.65rem; color:#444; font-weight:700; }
    .pred-drv  { min-width:36px; font-family:var(--mono); font-weight:800; font-size:0.8rem; color:var(--red); }
    .pred-team { flex:0 0 100px; font-size:0.68rem; color:var(--muted); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .pred-bar-bg { flex:1; background:rgba(255,255,255,0.05); border-radius:99px; height:5px; overflow:hidden; }
    .pred-bar  { height:100%; border-radius:99px; background:linear-gradient(90deg,var(--red-dim),var(--red-bright)); }
    .pred-pct  { min-width:40px; text-align:right; font-family:var(--mono); font-size:0.78rem; font-weight:700; color:var(--red); }

    /* ── Comparison cards ────────────────────────── */
    .p2p-cmp-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:0.6rem; margin-bottom:1.4rem; }
    .p2p-cmp-card {
        background:var(--surface2); border:1px solid var(--border);
        border-radius:12px; padding:0.9rem 0.75rem; text-align:center;
        transition: border-color 0.2s;
    }
    .p2p-cmp-card:hover { border-color:var(--border-hot); }
    .p2p-cmp-label { font-family:var(--mono); font-size:0.58rem; text-transform:uppercase; letter-spacing:0.1em; color:var(--muted); margin-bottom:0.5rem; }
    .p2p-cmp-val-a { font-size:1.1rem; font-weight:900; color:var(--red); }
    .p2p-cmp-val-b { font-size:1.1rem; font-weight:900; color:#ff6666; }
    .p2p-cmp-vs    { font-family:var(--mono); font-size:0.6rem; color:#333; margin:0.2rem 0; }

    /* ── Plotly ──────────────────────────────────── */
    [data-testid="stPlotlyChart"] {
        background:var(--surface) !important; border:1px solid var(--border) !important;
        border-radius:var(--radius) !important; padding:0.5rem 0.6rem 0.2rem !important;
        margin-bottom:0.85rem !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,0.03) !important;
    }
    .js-plotly-plot svg.main-svg { background:transparent !important; }
    .js-plotly-plot text { fill:#777 !important; font-family:var(--font) !important; }
    .js-plotly-plot g.gridlayer path { stroke:rgba(255,255,255,0.04) !important; }

    /* ── Tabs ────────────────────────────────────── */
    [data-testid="stTabs"] { border-bottom:1px solid var(--border) !important; margin-bottom:1.5rem !important; }
    [data-testid="stTabs"] button {
        font-family:var(--font) !important; font-weight:700 !important;
        font-size:0.72rem !important; text-transform:uppercase !important;
        letter-spacing:0.1em !important; color:var(--muted) !important;
        background:transparent !important; border:none !important;
        padding:0.6rem 1rem !important; border-radius:8px 8px 0 0 !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color:#fff !important; background:rgba(225,6,0,0.1) !important;
        border-bottom:2px solid var(--red) !important;
    }
    [data-testid="stTabs"] button:hover { color:#ccc !important; }

    /* ── Inputs ──────────────────────────────────── */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background:var(--surface) !important; border-color:var(--border) !important;
        color:#fff !important; border-radius:10px !important;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background:rgba(225,6,0,0.12) !important;
        border-color:var(--border-hot) !important; color:var(--red) !important;
    }
    div[data-baseweb="popover"] { background:#0a0a0a !important; }
    div[role="listbox"] {
        background:#0a0a0a !important; border:1px solid var(--border-hot) !important;
        border-radius:12px !important; box-shadow:var(--glow) !important;
    }
    div[role="option"] { background:#0a0a0a !important; color:#fff !important; font-family:var(--font) !important; }
    div[role="option"]:hover { background:rgba(225,6,0,0.15) !important; }
    div[aria-selected="true"] { background:rgba(225,6,0,0.25) !important; color:#fff !important; }
    [data-testid="stAlert"] {
        background:var(--surface) !important; border:1px solid var(--border) !important;
        color:var(--muted) !important; border-radius:10px !important;
    }

    /* ── Footer ──────────────────────────────────── */
    .p2p-footer {
        text-align:center; color:#2a2a2a; font-family:var(--mono);
        font-size:0.65rem; text-transform:uppercase; letter-spacing:0.18em;
        padding:2rem 0 0.5rem; border-top:1px solid var(--border); margin-top:2rem;
    }

    /* ── Responsive ──────────────────────────────── */
    @media (max-width: 900px) {
        .p2p-hero       { grid-template-columns:1fr 1fr; }
        .p2p-team-grid  { grid-template-columns:1fr; }
        .p2p-cmp-grid   { grid-template-columns:repeat(3,1fr); }
        .p2p-page-title { font-size:1.75rem; }
        .block-container{ padding:0 1.2rem 2rem !important; }
        .p2p-navbar     { margin:0 -1.2rem; padding:0 1.2rem; }
        .p2p-nav-link span { display:none; }
    }
"""

_JS_ANIM = """
    const obs = new MutationObserver(() => {
        doc.querySelectorAll(
            '.p2p-driver-row, .p2p-team-card, .p2p-race-card, .p2p-metric-card, .p2p-pred-card'
        ).forEach((el, i) => {
            if (!el.dataset.animated) {
                el.dataset.animated = '1';
                el.style.animationDelay = (i * 0.04) + 's';
                el.classList.add('fade-up');
            }
        });
    });
    obs.observe(doc.body, { childList: true, subtree: true });
"""


def inject_styles():
    st.html(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700&display=swap');
        </style>
        <script>
        (function() {{
            const doc = window.parent.document;
            if (doc.getElementById('p2p-styles')) return;

            const s = doc.createElement('style');
            s.id = 'p2p-styles';
            s.textContent = {repr(CSS)};
            doc.head.appendChild(s);

            {_JS_ANIM}
        }})();
        </script>
        """
    )