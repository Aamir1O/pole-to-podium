 
<div align="center">

<img src="https://img.shields.io/badge/F1-Pole%20to%20Podium-e10600?style=for-the-badge&logoColor=white" />

<br /><br />

**A full-stack Formula 1 analytics platform.**
Live standings, ML-powered race predictions, tyre strategy analysis, and driver & constructor comparisons — built for the 2026 season and beyond.

<br />

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat-square&logo=postgresql&logoColor=white)
![XGBoost](https://img.shields.io/badge/Model-XGBoost-189AB4?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)

</div>

---

## Overview

Pole to Podium is a data platform for Formula 1 built in Python and Streamlit. It pulls live race data from a PostgreSQL database, runs an XGBoost win probability model after each qualifying session, and presents everything through a six-page dashboard designed around a single principle — charts first, everything else second.

The visual design is intentionally close to a professional trading terminal. Dark background, red accents, high information density, no decorative elements.

---

## Project Structure

```
pole-to-podium/
│
├── app.py                        # Entry point — data loading, routing, session state
├── check.py                      # DB connection and schema validation helper
├── requirements.txt
├── .gitignore
│
├── components/
│   ├── navbar.py                 # Sticky top navbar with active page state
│   ├── cards.py                  # Hero stats, race cards, metric cards, comparison grid
│   ├── charts.py                 # All 18 Plotly chart functions
│   └── standings.py              # Driver rows, team cards, prediction list renderer
│
├── pages/
│   ├── dashboard.py              # Championship battle, standings preview, schedule, win prob
│   ├── drivers.py                # Driver standings + two-driver comparison tool
│   ├── teams.py                  # Constructor standings + two-team comparison tool
│   ├── predictions.py            # Race weekend intelligence — model output and insights
│   ├── analytics.py              # Per-race deep dive — lap times, tyres, pace, positions
│   └── archive.py                # Complete 2025 season record
│
├── styles/
│   └── theme.py                  # Full CSS design system injected into Streamlit
│
├── utils/
│   ├── data.py                   # DB engine, load_data(), filter_season(), get_seasons()
│   ├── helpers.py                # Shared UI helpers — esc(), page_head(), themed(), show_chart()
│   └── predictions.py            # load_model(), build_predictions()
│
├── notebooks/
│   ├── 01_EDA.ipynb              # Exploratory data analysis
│   └── 02_model.ipynb            # Model training and evaluation
│
├── pipeline/                     # Data ingestion and processing scripts
├── data/                         # Raw and processed local data
└── model/
    ├── model.pkl                 # Trained XGBoost classifier
    └── encoders.pkl              # Label encoders + feature list
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL instance (local or hosted)
- Model files in `model/` — `model.pkl` and `encoders.pkl`

### Install

```bash
git clone https://github.com/Aamir1O/pole-to-podium.git
cd pole-to-podium
pip install -r requirements.txt
```

### Configure

Create a `.env` file in the root directory:

```env
DB_URL=postgresql://user:password@host:port/dbname
```

### Run

```bash
streamlit run app.py
```

---

## Database Schema

Four tables are required:

```sql
results (
    year          INT,
    race_id       TEXT,
    race_name     TEXT,
    circuit       TEXT,
    date          DATE,
    driver        TEXT,
    team          TEXT,
    finish_pos    INT,
    grid_pos      INT,
    points        FLOAT,
    sprint_pts    FLOAT
)

qualifying (
    race_id       TEXT,
    driver        TEXT,
    grid_pos      INT,
    q1_secs       FLOAT,
    q2_secs       FLOAT,
    q3_secs       FLOAT
)

laps (
    race_id          TEXT,
    driver           TEXT,
    lap_number       INT,
    lap_time_secs    FLOAT,
    tyre_compound    TEXT,
    tyre_age         INT
)

weather (
    race_id          TEXT,
    avg_track_temp   FLOAT,
    avg_humidity     FLOAT,
    rainfall         INT
)
```

---

## Pages

**Dashboard**
Season overview. Championship battle chart sits at the top as the primary visual. Below it — driver standings, race schedule, constructor standings, and a win probability preview for the next race.

**Drivers**
Full driver standings for the current season. Comparison tool lets you select any two drivers and shows points progression, finishing position trend, and a head-to-head chart side by side.

**Teams**
Constructor standings. Comparison tool shows team points progression, average qualifying position, driver contribution breakdown per team, and race pace.

**Predictions**
Race weekend intelligence center. Runs the XGBoost model against the latest qualifying data and surfaces the top 3 predicted finishers, a full win probability distribution chart, and a ranked table of all drivers.

**Analytics**
Per-race analysis. Select any race from the season and drill into lap time evolution, tyre strategy, tyre degradation, grid-to-finish position changes, qualifying vs race result scatter, and race pace distribution.

**Archive**
Complete 2025 season. Final driver and constructor standings, all race results, tyre strategy breakdowns, and driver-level statistics.

---

## Prediction Model

An XGBoost classifier trained on historical F1 race outcomes. Predictions are generated fresh after each qualifying session.

| Feature | Source |
|---------|--------|
| Grid position | `qualifying` |
| Q3 lap time | `qualifying` |
| Historical win rate | `results` (aggregated) |
| Average lap time | `laps` (aggregated) |
| Track temperature | `weather` |
| Humidity | `weather` |
| Rainfall | `weather` |
| Circuit encoding | Label encoder |
| Driver encoding | Label encoder |
| Team encoding | Label encoder |

Model training and evaluation notebooks are in `notebooks/`.

---

## Multi-Season Support

No season is hardcoded. `utils/data.py` reads all distinct years from the database via `get_seasons()` and `filter_season(year)` scopes data to any given year. When 2027 data is ingested, it becomes available automatically across all pages.

---

## Tech Stack

| | |
|-|---|
| UI | Streamlit |
| Charts | Plotly |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| ML | XGBoost |
| Styling | Custom CSS injected via Streamlit components |
| Fonts | Outfit · JetBrains Mono |

---

## Design

```
Background    #030303
Surface       rgba(14, 14, 14, 0.92)
Accent        #e10600
Text          #f2f2f2
Muted         #6b6b6b
```

Inspired by Formula1.com, TradingView, and Bloomberg Terminal.

---

## Roadmap

- Live timing integration
- Driver profile subpages
- Cross-season comparison tool
- Export to PDF and CSV
- Mobile layout

---

<div align="center">

Pole to Podium 

</div>