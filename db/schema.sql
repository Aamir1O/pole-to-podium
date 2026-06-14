-- Run once to set up the corner analysis tables.
-- Safe to re-run: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS sessions_f1 (
    id              SERIAL PRIMARY KEY,
    season          INTEGER NOT NULL,
    round           INTEGER NOT NULL,
    circuit_key     TEXT NOT NULL,
    session_type    TEXT NOT NULL,       -- 'FP1','FP2','FP3','Q','R'
    session_date    DATE,
    total_distance  FLOAT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (season, round, session_type)
);

-- Note: named sessions_f1 to avoid collision with any 'sessions'
-- table that might exist from your CSV pipeline.

CREATE TABLE IF NOT EXISTS corners (
    id              SERIAL PRIMARY KEY,
    circuit_key     TEXT NOT NULL,
    corner_number   INTEGER NOT NULL,
    corner_name     TEXT,
    dist_start_m    FLOAT NOT NULL,
    dist_apex_m     FLOAT NOT NULL,
    dist_end_m      FLOAT NOT NULL,
    UNIQUE (circuit_key, corner_number)
);

CREATE TABLE IF NOT EXISTS telemetry_laps (
    id              SERIAL PRIMARY KEY,
    session_id      INTEGER REFERENCES sessions_f1(id),
    driver_code     TEXT NOT NULL,
    lap_number      INTEGER NOT NULL,
    lap_time_s      FLOAT,
    is_fastest      BOOLEAN DEFAULT FALSE,
    compound        TEXT,
    tyre_life       INTEGER,
    UNIQUE (session_id, driver_code, lap_number)
);

-- Telemetry stored as Postgres arrays (efficient, no join needed per sample)
CREATE TABLE IF NOT EXISTS telemetry_channels (
    id              SERIAL PRIMARY KEY,
    lap_id          INTEGER REFERENCES telemetry_laps(id) UNIQUE,
    distance_m      FLOAT[]  NOT NULL,
    speed_kph       FLOAT[]  NOT NULL,
    throttle_pct    FLOAT[]  NOT NULL,
    brake           BOOLEAN[],
    rpm             INTEGER[],
    gear            INTEGER[],
    x_pos           FLOAT[],
    y_pos           FLOAT[],
    sample_count    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS corner_metrics (
    id                      SERIAL PRIMARY KEY,
    lap_id                  INTEGER REFERENCES telemetry_laps(id),
    corner_id               INTEGER REFERENCES corners(id),
    entry_speed_kph         FLOAT,
    brake_point_m           FLOAT,
    brake_duration_m        FLOAT,
    apex_speed_kph          FLOAT,
    apex_dist_m             FLOAT,
    exit_speed_kph          FLOAT,
    throttle_point_m        FLOAT,
    time_to_full_throttle_s FLOAT,
    entry_score             FLOAT,
    apex_score              FLOAT,
    exit_score              FLOAT,
    cpi                     FLOAT,
    corner_time_s           FLOAT,
    UNIQUE (lap_id, corner_id)
);

CREATE TABLE IF NOT EXISTS driver_profiles (
    id                      SERIAL PRIMARY KEY,
    session_id              INTEGER REFERENCES sessions_f1(id),
    driver_code             TEXT NOT NULL,
    style_label             TEXT NOT NULL,
    style_confidence        FLOAT,
    braking_aggressiveness  FLOAT,
    apex_commitment         FLOAT,
    traction_efficiency     FLOAT,
    entry_speed_index       FLOAT,
    throttle_progression    FLOAT,
    high_speed_advantage    FLOAT,
    low_speed_advantage     FLOAT,
    UNIQUE (session_id, driver_code)
);

CREATE TABLE IF NOT EXISTS delta_traces (
    id          SERIAL PRIMARY KEY,
    session_id  INTEGER REFERENCES sessions_f1(id),
    driver_a    TEXT NOT NULL,
    driver_b    TEXT NOT NULL,
    distance_m  FLOAT[] NOT NULL,
    delta_s     FLOAT[] NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (session_id, driver_a, driver_b)
);