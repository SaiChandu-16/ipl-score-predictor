import pickle
import numpy as np
import os
import logging
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

# Global model object
_model = None
_model_version = "v0.0.0"

HF_REPO_ID = os.getenv("HF_REPO_ID", "your-username/ipl-score-predictor")

# Venue average scores — used as fallback features
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

PITCH_SCORE_MODIFIER = {
    "Flat": 15,
    "Dry": 0,
    "Dusty": -10,
    "Grassy": -5,
    "Spin Friendly": -8,
    "Pace Friendly": -5,
}


def load_model():
    """Load model from Hugging Face Hub."""
    global _model, _model_version
    try:
        model_path = hf_hub_download(repo_id=HF_REPO_ID, filename="model.pkl")
        with open(model_path, "rb") as f:
            _model = pickle.load(f)
        
        # Try to load version metadata
        try:
            version_path = hf_hub_download(repo_id=HF_REPO_ID, filename="version.txt")
            with open(version_path) as f:
                _model_version = f.read().strip()
        except Exception:
            _model_version = "v1.0.0"

        logger.info(f"Model loaded: {_model_version}")
    except Exception as e:
        logger.warning(f"Could not load model from HuggingFace: {e}. Using heuristic fallback.")
        _model = None
        _model_version = "heuristic-v0"


def get_model_version() -> str:
    return _model_version


def extract_features(data: dict) -> np.ndarray:
    """
    Convert match input into a feature vector.
    Expand this as your model evolves.
    """
    venue_avg = VENUE_AVG_SCORES.get(data["venue"], VENUE_AVG_SCORES["default"])
    pitch_modifier = PITCH_SCORE_MODIFIER.get(data["pitch_type"], 0)
    toss_advantage = 5 if (
        data["toss_winner"] == data["batting_team"] and data["toss_decision"] == "Bat"
    ) else -3
    dew_bonus = 8 if data.get("dew_factor") else 0
    day_bonus = -5 if data.get("match_time") == "Day" else 0
    num_batters = len(data.get("batting_team_players", []))

    features = np.array([
        venue_avg,
        pitch_modifier,
        toss_advantage,
        dew_bonus,
        day_bonus,
        data.get("pitch_hardness", 7),
        num_batters,
    ]).reshape(1, -1)

    return features


def predict_score(data: dict) -> dict:
    """Run prediction and return score + breakdown."""
    features = extract_features(data)

    if _model is not None:
        predicted = int(_model.predict(features)[0])
    else:
        # Heuristic fallback when no model is trained yet
        venue_avg = VENUE_AVG_SCORES.get(data["venue"], VENUE_AVG_SCORES["default"])
        pitch_mod = PITCH_SCORE_MODIFIER.get(data["pitch_type"], 0)
        toss_mod = 5 if (
            data["toss_winner"] == data["batting_team"] and data["toss_decision"] == "Bat"
        ) else -3
        dew_mod = 8 if data.get("dew_factor") else 0
        predicted = venue_avg + pitch_mod + toss_mod + dew_mod

    # Phase breakdown (heuristic split: 30% powerplay, 35% middle, 35% death)
    powerplay = int(predicted * 0.30)
    middle = int(predicted * 0.35)
    death = predicted - powerplay - middle

    return {
        "predicted_score": predicted,
        "confidence_range": {"low": predicted - 12, "high": predicted + 12},
        "phase_breakdown": {
            "powerplay": powerplay,
            "middle_overs": middle,
            "death_overs": death,
        },
    }
