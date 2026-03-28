"""
training/retrain.py
-------------------
Automated retraining script triggered by GitHub Actions weekly.
Pulls labeled data from Supabase, retrains, evaluates, and pushes
the new model to Hugging Face only if it's better than the current one.
"""

import os
import pickle
import logging
import datetime
import numpy as np
import pandas as pd
from supabase import create_client
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
from huggingface_hub import HfApi, hf_hub_download

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
HF_REPO_ID   = os.environ["HF_REPO_ID"]
HF_TOKEN     = os.environ["HF_TOKEN"]

MIN_NEW_SAMPLES = 10  # Don't retrain unless we have at least 10 new labeled rows


def pull_labeled_data() -> pd.DataFrame:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = client.table("predictions")\
        .select("*")\
        .not_.is_("actual_score", "null")\
        .execute()
    rows = result.data
    logger.info(f"Fetched {len(rows)} labeled rows from Supabase")
    return pd.DataFrame(rows)


def flatten_inputs(df: pd.DataFrame) -> pd.DataFrame:
    """Expand the JSONB 'inputs' column into flat feature columns."""
    inputs_df = pd.json_normalize(df["inputs"])
    flat = pd.concat([inputs_df, df[["actual_score"]]], axis=1)
    return flat


def build_features(df: pd.DataFrame) -> tuple:
    """Reuse same feature logic as train.py."""
    from training.train import build_features as _build, VENUE_AVG_SCORES, PITCH_MODIFIERS

    # Map column names from Supabase JSON to expected columns
    df = df.rename(columns={
        "pitch_hardness": "pitch_hardness",
        "dew_factor": "dew_factor",
        "toss_winner": "toss_winner",
        "batting_team": "batting_team",
        "toss_decision": "toss_decision",
        "match_time": "match_time",
        "season": "season",
    })
    if "num_batting_players" not in df.columns:
        df["num_batting_players"] = df["batting_team_players"].apply(
            lambda x: len(x) if isinstance(x, list) else 6
        )

    X = _build(df)
    y = df["actual_score"]
    return X, y


def load_current_model():
    try:
        path = hf_hub_download(repo_id=HF_REPO_ID, filename="model.pkl", token=HF_TOKEN)
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        logger.warning("No current model on HuggingFace. Will push new one unconditionally.")
        return None


def push_model(model, mae: float):
    with open("model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open("version.txt", "w") as f:
        f.write(f"v{datetime.date.today().isoformat()}-mae{mae:.1f}")

    api = HfApi()
    api.upload_file(path_or_fileobj="model.pkl", path_in_repo="model.pkl",
                    repo_id=HF_REPO_ID, repo_type="model", token=HF_TOKEN)
    api.upload_file(path_or_fileobj="version.txt", path_in_repo="version.txt",
                    repo_id=HF_REPO_ID, repo_type="model", token=HF_TOKEN)
    logger.info(f"✅ New model pushed to HuggingFace. MAE={mae:.1f}")


def main():
    df_raw = pull_labeled_data()

    if len(df_raw) < MIN_NEW_SAMPLES:
        logger.info(f"Only {len(df_raw)} labeled samples. Need {MIN_NEW_SAMPLES}. Skipping retrain.")
        return

    df_flat = flatten_inputs(df_raw)
    X, y = build_features(df_flat)

    # Train new model
    new_model = XGBRegressor(
        n_estimators=300, learning_rate=0.05, max_depth=5,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
    )
    new_model.fit(X, y)
    new_mae = mean_absolute_error(y, new_model.predict(X))
    logger.info(f"New model MAE: {new_mae:.1f}")

    # Compare with current model
    current_model = load_current_model()
    if current_model is not None:
        old_mae = mean_absolute_error(y, current_model.predict(X))
        logger.info(f"Current model MAE: {old_mae:.1f}")
        if new_mae >= old_mae:
            logger.info("❌ New model is not better. Keeping current model.")
            return

    push_model(new_model, new_mae)


if __name__ == "__main__":
    main()
