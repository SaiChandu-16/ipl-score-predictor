import os
import uuid
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

_client: Client = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def save_prediction(inputs: dict, predicted_score: int, confidence_range: dict,
                    phase_breakdown: dict, model_version: str) -> str:
    """Save a prediction to the DB and return the prediction ID."""
    prediction_id = str(uuid.uuid4())
    client = get_client()
    client.table("predictions").insert({
        "id": prediction_id,
        "inputs": inputs,
        "predicted_score": predicted_score,
        "confidence_range": confidence_range,
        "phase_breakdown": phase_breakdown,
        "model_version": model_version,
        "actual_score": None,
        "user_rating": None,
    }).execute()
    logger.info(f"Saved prediction {prediction_id}")
    return prediction_id


def save_feedback(prediction_id: str, actual_score: int,
                  user_rating: int = None, comments: str = None):
    """Update a prediction row with actual score and user feedback."""
    client = get_client()
    update_data = {
        "actual_score": actual_score,
        "user_rating": user_rating,
        "feedback_comments": comments,
    }
    client.table("predictions").update(update_data).eq("id", prediction_id).execute()
    logger.info(f"Saved feedback for {prediction_id}: actual={actual_score}")


def get_prediction_history(limit: int = 50) -> list:
    """Fetch recent predictions with feedback."""
    client = get_client()
    result = client.table("predictions")\
        .select("id, created_at, inputs, predicted_score, actual_score, user_rating, model_version")\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    return result.data


def get_labeled_data() -> list:
    """Fetch all predictions that have actual scores — used for retraining."""
    client = get_client()
    result = client.table("predictions")\
        .select("*")\
        .not_.is_("actual_score", "null")\
        .execute()
    return result.data
