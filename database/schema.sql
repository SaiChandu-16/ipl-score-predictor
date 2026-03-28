-- =============================================================
-- IPL Score Predictor — Supabase Schema v2
-- Run this in Supabase → SQL Editor → New Query → Run
-- =============================================================

-- ── Teams ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teams (
    name               TEXT PRIMARY KEY,
    short_name         TEXT,
    espncricinfo_id    TEXT,
    home_ground        TEXT,
    updated_at         TIMESTAMPTZ DEFAULT now()
);

-- ── Players (live IPL squads) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS players (
    id                 BIGSERIAL PRIMARY KEY,
    name               TEXT NOT NULL,
    team_name          TEXT NOT NULL REFERENCES teams(name),
    role               TEXT,              -- Batter, Bowler, All-rounder, WK-Batter
    country            TEXT DEFAULT 'India',
    espncricinfo_id    TEXT,
    is_active          BOOLEAN DEFAULT TRUE,
    updated_at         TIMESTAMPTZ DEFAULT now(),

    UNIQUE (name, team_name)
);

CREATE INDEX IF NOT EXISTS idx_players_team ON players (team_name) WHERE is_active = TRUE;

-- ── Match data (from Cricsheet — used for training) ────────────
CREATE TABLE IF NOT EXISTS match_data (
    id                  BIGSERIAL PRIMARY KEY,
    cricsheet_match_id  TEXT UNIQUE NOT NULL,
    season              INT,
    match_date          DATE,
    venue               TEXT,
    batting_team        TEXT,
    bowling_team        TEXT,
    toss_winner         TEXT,
    toss_decision       TEXT,
    innings_score       INT,
    innings_wickets     INT,
    pitch_type          TEXT DEFAULT 'Flat',
    pitch_hardness      INT  DEFAULT 7,
    dew_factor          BOOLEAN DEFAULT FALSE,
    match_time          TEXT DEFAULT 'Evening',
    num_batting_players INT  DEFAULT 6,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_match_data_season ON match_data (season);
CREATE INDEX IF NOT EXISTS idx_match_data_venue  ON match_data (venue);

-- ── Predictions (user predictions + feedback) ──────────────────
CREATE TABLE IF NOT EXISTS predictions (
    id               UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at       TIMESTAMPTZ DEFAULT now(),
    inputs           JSONB       NOT NULL,
    predicted_score  INT         NOT NULL,
    confidence_range JSONB,
    phase_breakdown  JSONB,
    model_version    TEXT,
    actual_score     INT,
    user_rating      SMALLINT    CHECK (user_rating BETWEEN 1 AND 5),
    feedback_comments TEXT
);

CREATE INDEX IF NOT EXISTS idx_predictions_labeled
    ON predictions (actual_score) WHERE actual_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_predictions_created_at
    ON predictions (created_at DESC);

-- ── App metadata (last sync timestamps etc.) ───────────────────
CREATE TABLE IF NOT EXISTS app_metadata (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO app_metadata (key, value) VALUES
    ('rosters_last_updated',   NULL),
    ('match_data_last_synced', NULL)
ON CONFLICT (key) DO NOTHING;

-- ── Useful views ───────────────────────────────────────────────

CREATE OR REPLACE VIEW model_accuracy AS
SELECT
    model_version,
    COUNT(*)                                             AS total_predictions,
    COUNT(actual_score)                                  AS labeled_count,
    ROUND(AVG(ABS(predicted_score - actual_score)), 1)  AS avg_abs_error_runs,
    ROUND(AVG(user_rating), 2)                          AS avg_user_rating,
    MIN(created_at)                                      AS first_prediction,
    MAX(created_at)                                      AS last_prediction
FROM predictions
WHERE actual_score IS NOT NULL
GROUP BY model_version
ORDER BY last_prediction DESC;
