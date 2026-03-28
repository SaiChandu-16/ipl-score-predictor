from fastapi import APIRouter, HTTPException, Query
from app.services.db_service import get_prediction_history
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def prediction_history(limit: int = Query(default=20, le=100)):
    """
    Fetch recent predictions with their actual scores (if submitted).
    Useful for showing users past predictions and model accuracy.
    """
    try:
        records = get_prediction_history(limit=limit)
        # Compute accuracy stats
        labeled = [r for r in records if r.get("actual_score")]
        avg_error = None
        if labeled:
            errors = [abs(r["predicted_score"] - r["actual_score"]) for r in labeled]
            avg_error = round(sum(errors) / len(errors), 1)

        return {
            "total": len(records),
            "labeled_count": len(labeled),
            "avg_abs_error_runs": avg_error,
            "records": records,
        }
    except Exception as e:
        logger.error(f"History fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
