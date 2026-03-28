from fastapi import APIRouter, HTTPException
from app.models.schemas import FeedbackInput
from app.services.db_service import save_feedback
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/")
async def submit_feedback(data: FeedbackInput):
    """
    Submit the actual match score after the game.
    This labeled data is used to retrain the model weekly.
    """
    try:
        save_feedback(
            prediction_id=data.prediction_id,
            actual_score=data.actual_score,
            user_rating=data.user_rating,
            comments=data.comments,
        )
        return {
            "status": "success",
            "message": "Thank you! Your feedback helps improve predictions 🏏",
        }
    except Exception as e:
        logger.error(f"Feedback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
