from fastapi import APIRouter, HTTPException
from app.models.schemas import MatchInput, PredictionResponse
from app.services.model_service import predict_score, get_model_version
from app.services.db_service import save_prediction
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=PredictionResponse)
async def make_prediction(data: MatchInput):
    """
    Predict the IPL innings score given:
    - Playing 12 (batting + bowling teams)
    - Pitch report
    - Toss result
    """
    try:
        input_dict = data.dict()
        result = predict_score(input_dict)
        model_version = get_model_version()

        prediction_id = save_prediction(
            inputs=input_dict,
            predicted_score=result["predicted_score"],
            confidence_range=result["confidence_range"],
            phase_breakdown=result["phase_breakdown"],
            model_version=model_version,
        )

        return PredictionResponse(
            prediction_id=prediction_id,
            predicted_score=result["predicted_score"],
            confidence_range=result["confidence_range"],
            phase_breakdown=result["phase_breakdown"],
            model_version=model_version,
        )

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
