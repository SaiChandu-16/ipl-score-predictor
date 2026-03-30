from fastapi import APIRouter, HTTPException
from app.models.schemas import MatchInput, PredictionResponse
from app.services.model_service import predict_score, get_model_version
from app.services.db_service import save_prediction
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=PredictionResponse)
async def make_prediction(data: MatchInput):
    try:
        # ✅ model_dump_json() + json.loads() guarantees all enums become
        #    plain strings before hitting Supabase JSONB — no serialization errors
        input_dict = json.loads(data.model_dump_json())

        result        = predict_score(input_dict)
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
        # ✅ Log full traceback — visible in Render logs
        logger.exception(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))