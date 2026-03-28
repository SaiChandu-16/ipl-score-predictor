"""
training/train.py
-----------------
Initial training script using Cricsheet IPL data.
Run locally first to produce model.pkl, then push to Hugging Face.

Usage:
    python training/train.py --data data/ipl_matches.csv
"""

import argparse
import pandas as pd
import numpy as np
import pickle
import logging
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Feature engineering ───────────────────────────────────────────

VENUE_AVG_SCORES = {
    "Wankhede Stadium": 175,
    "M Chinnaswamy Stadium": 185,
    "Eden Gardens": 160,
    "MA Chidambaram Stadium": 155,
    "Arun Jaitley Stadium": 165,
    "Rajiv Gandhi International Stadium": 170,
    "Punjab Cricket Association Stadium": 172,
    "Sawai Mansingh Stadium": 163,
    "default": 165,
}

PITCH_MODIFIERS = {
    "Flat": 15, "Dry": 0, "Dusty": -10,
    "Grassy": -5, "Spin Friendly": -8, "Pace Friendly": -5,
}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw match DataFrame into model feature matrix.
    
    Expected columns in df:
        venue, pitch_type, pitch_hardness, dew_factor,
        toss_winner, batting_team, toss_decision,
        match_time, season, num_batting_players
    """
    df = df.copy()

    df["venue_avg"] = df["venue"].map(VENUE_AVG_SCORES).fillna(165)
    df["pitch_mod"] = df["pitch_type"].map(PITCH_MODIFIERS).fillna(0)
    df["toss_advantage"] = np.where(
        (df["toss_winner"] == df["batting_team"]) & (df["toss_decision"] == "Bat"), 5, -3
    )
    df["dew_bonus"] = df["dew_factor"].astype(int) * 8
    df["day_penalty"] = np.where(df["match_time"] == "Day", -5, 0)
    df["season_norm"] = (df["season"] - 2008) / (2024 - 2008)

    feature_cols = [
        "venue_avg", "pitch_mod", "toss_advantage",
        "dew_bonus", "day_penalty", "pitch_hardness",
        "num_batting_players", "season_norm"
    ]
    return df[feature_cols]


def train(data_path: str, output_path: str = "model.pkl"):
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    required = ["venue", "pitch_type", "pitch_hardness", "dew_factor",
                 "toss_winner", "batting_team", "toss_decision",
                 "match_time", "season", "num_batting_players", "innings_score"]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in data: {missing}")

    X = build_features(df)
    y = df["innings_score"]

    # Time-based split — train on older seasons, test on newer
    split_idx = int(len(df) * 0.85)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    logger.info(f"Training on {len(X_train)} samples, testing on {len(X_test)}")

    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50,
    )

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    within_10 = np.mean(np.abs(preds - y_test) <= 10) * 100

    logger.info(f"✅ MAE: {mae:.1f} runs | Within ±10 runs: {within_10:.1f}%")

    with open(output_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {output_path}")

    with open("version.txt", "w") as f:
        import datetime
        f.write(f"v{datetime.date.today().isoformat()}-mae{mae:.1f}")

    return mae


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/ipl_matches.csv")
    parser.add_argument("--output", default="model.pkl")
    args = parser.parse_args()
    train(args.data, args.output)
