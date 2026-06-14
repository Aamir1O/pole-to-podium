# 🏁 Pole to Podium

<div align="center">

<img src="https://img.shields.io/badge/Formula%201-Pole%20to%20Podium-e10600?style=for-the-badge&logoColor=white" />

<br /><br />

**A full-stack, production-grade F1 telemetry analytics and machine learning prediction platform.**  
Powered by a **Next.js** frontend, a **FastAPI** backend, and an advanced **FastF1/XGBoost** ingestion pipeline.

<br />

[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-black?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![XGBoost](https://img.shields.io/badge/ML%20Engine-XGBoost-189AB4?style=flat-square)](https://xgboost.readthedocs.io)

</div>

---

## 🛠️ Project Overview

**Pole to Podium** is an advanced data-driven application for Formula 1 fans and race engineers. The platform combines core championship metrics, historical data, and deep telemetry traces to analyze driver techniques down to individual corners. It runs predictive machine learning models to calculate driver win probabilities after qualifying sessions.

The system is structured as a monorepo containing:
1. **Frontend**: A highly optimized React application built in Next.js (TypeScript) adopting a modern dark-mode HUD UI.
2. **Backend**: A REST API built with FastAPI that delivers data, computed telemetry metrics, dynamic charts, and model prediction distributions.
3. **Telemetry & Data Pipeline**: A suite of Python scripts utilizing the FastF1 API to ingest, resample, and analyze speed, throttle, and brake traces, saving everything in a PostgreSQL database.
4. **Machine Learning Model**: An XGBoost classifier that predicts race outcomes based on grid positions, Q3 times, and historical driver/constructor performance.

---

## 📂 Codebase Structure

- **[backend/](backend)**: FastAPI application layer.
  - **[backend/main.py](backend/main.py)**: API entry point containing CORS configuration and API route registration.
  - **[backend/routers/](backend/routers)**: Modular endpoint routers for Status, Dashboard, Drivers, Teams, Predictions, Telemetry, and Race Analytics.
  - **[backend/services/](backend/services)**: Core business logic wrappers, including:
    - `db_service.py` for database queries and mapping telemetry.
    - `prediction_service.py` to calculate probability tables using the serialized model.
  - **[backend/utils/](backend/utils)**: Utility scripts including Plotly chart generators (`charts.py`) and design metadata styling (`metadata.py`).
- **[frontend/](frontend)**: Next.js frontend application.
  - **[frontend/src/app/](frontend/src/app)**: Router structure with pages for `/analytics`, `/drivers`, `/predictions`, `/race-center`, `/teams`, and `/telemetry`.
  - **[frontend/src/components/](frontend/src/components)**: Shared components such as the navigation header (`Navbar.tsx`) and the client-side Plotly wrapper (`PlotlyChart.tsx`).
- **[pipeline/](pipeline)**: Scripts to ingest, align, process, and save telemetry.
  - **[pipeline/session_loader.py](pipeline/session_loader.py)**: High-level loader that coordinates telemetry downloads, alignments, corner detections, time delta traces, and DB loading.
  - **[pipeline/telemetry_aligner.py](pipeline/telemetry_aligner.py)**: Resamples raw, variable-frequency telemetry from FastF1 into a uniform 300-point grid.
  - **[pipeline/corner_detector.py](pipeline/corner_detector.py)**: Identifies corners along a track segment using speed deceleration signatures.
  - **[pipeline/cpi_calculator.py](pipeline/cpi_calculator.py)**: Evaluates corner telemetry to output a Corner Performance Index (CPI).
  - **[pipeline/delta_calculator.py](pipeline/delta_calculator.py)**: Performs numerical integration on speed profiles to extract spatial time differences.
  - **[pipeline/predict_next_race.py](pipeline/predict_next_race.py)**: Feeds qualifying features into the trained XGBoost model.
- **[db/](db)**: PostgreSQL connection utilities and database schema definition.
  - **[db/schema.sql](db/schema.sql)**: Structure for sessions, corners, telemetry channels, metrics, and profiles.
- **[model/](model)**: Serialized XGBoost model (`model.pkl`) and categorical encoders (`encoders.pkl`).
- **[notebooks/](notebooks)**: Jupyter notebooks for exploratory data analysis (`01_EDA.ipynb`) and model training (`02_model.ipynb`).

---

## ⚡ Database Schema

The analytics pipeline reads from and writes to 7 key tables defined in **[db/schema.sql](db/schema.sql)**:

| Table | Description |
|---|---|
| `sessions_f1` | Session-level context (e.g. season, round, circuit, session type). |
| `corners` | Track coordinates defining specific corner numbers and boundaries. |
| `telemetry_laps` | Metadata for specific laps (e.g. driver, lap number, lap time, compound, age). |
| `telemetry_channels` | Time-series telemetry arrays (distance, speed, throttle, brake, rpm, gear, x/y position) resampled to a consistent 300-sample grid. |
| `corner_metrics` | Micro-metrics per corner (entry speed, brake points, apex speed, exit speed, CPI score). |
| `driver_profiles` | Aggregated driver styling indices (braking aggressiveness, traction efficiency, high/low speed advantages). |
| `delta_traces` | Spatial delta arrays mapping cumulative time gains/losses between drivers along the lap. |

---

## 🚦 Ingestion and Analytics Pipeline

The core telemetry pipeline works by aligning raw, irregular time-series data:

```
[Raw FastF1 Telemetry] ────> [Telemetry Aligner] ────> [Corner Detector] ────> [CPI & Delta Calculator]
     (driver A & B)          (Resample to 300 grid)    (Detect boundaries)     (Save metrics to DB)
```

1. **Alignment**: Since telemetry sampling rates fluctuate, the **[pipeline/telemetry_aligner.py](pipeline/telemetry_aligner.py)** interpolates telemetry signals against a standardized spatial 300-point grid.
2. **Corner Detection**: Deceleration zones are identified automatically in **[pipeline/corner_detector.py](pipeline/corner_detector.py)** and correlated with circuit keys.
3. **Corner Performance Index (CPI)**: Evaluated in **[pipeline/cpi_calculator.py](pipeline/cpi_calculator.py)**, calculating entrance speed index, apex speeds, and traction throttle application rates.
4. **Delta Tracing**: Distance-based delta traces are computed in **[pipeline/delta_calculator.py](pipeline/delta_calculator.py)** to show *exactly* where a driver gains or loses time (e.g., Turn 4 entry vs. exit).

---

## 🚀 Getting Started

### 1. Prerequisites

Ensure you have the following installed on your machine:
- **Python 3.9+**
- **Node.js 18+** (for Next.js)
- A **PostgreSQL** instance (hosted or local, e.g. Supabase)

---

### 2. Configuration

Create a **[.env](.env)** file in the project root directory and add your connection string:

```env
DB_URL=postgresql://username:password@host:port/database_name?connect_timeout=10
```

---

### 3. Database Initialization

To set up your database schema, run the schema execution script:

```bash
python db/run_schema.py
```

---

### 4. Running the Backend (FastAPI)

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
2. Install Python requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the API development server using Uvicorn:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
4. Verify by opening [http://localhost:8000/](http://localhost:8000/) or access the interactive API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

---

### 5. Running the Frontend (Next.js)

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to [http://localhost:3000](http://localhost:3000).

---

### 6. Loading Telemetry via Pipeline

To download and process a specific session telemetry (e.g., 2026 Season, Round 1 Bahrain GP, Qualifying, comparing VER vs. NOR):

```bash
python pipeline/session_loader.py --season 2026 --round 1 --session Q --driver_a VER --driver_b NOR
```

To run a prediction for the next race weekend using the XGBoost engine:

```bash
python pipeline/predict_next_race.py
```

---

## 🧠 ML Prediction Model Features

The XGBoost model processes the following features to output win probabilities:

* **Grid Position** (from qualifying results)
* **Q3 / Best Qualy Lap Time**
* **Driver Win Rate** (aggregated historically)
* **Average Lap Time** (from race lap history)
* **Weather Conditions** (Track temperature, humidity, rainfall index)
* **Circuit, Driver, & Team** (Label encoded)

You can explore or run model training in the notebook **[notebooks/02_model.ipynb](notebooks/02_model.ipynb)**.

---

<div align="center">
Developed by <b>Aamir</b> · 2026  
<i>Accelerating F1 metrics into data science.</i>
</div>