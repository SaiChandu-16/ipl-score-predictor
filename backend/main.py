from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import predict, feedback, history, teams
from app.services.model_service import load_model
from app.services.cricket_data_service import refresh_all_rosters, get_rosters_last_updated
import logging
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IPL Score Predictor API",
    description="Predict IPL innings scores with live team rosters and pitch reports.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # 1. Load ML model from Hugging Face
    logger.info("Loading model from Hugging Face...")
    load_model()
    logger.info("Model loaded.")

    # 2. Refresh rosters only if data is stale (> 24 hours old)
    last_updated = get_rosters_last_updated()
    should_refresh = True

    if last_updated:
        try:
            last_dt = datetime.datetime.fromisoformat(last_updated)
            age_hours = (datetime.datetime.utcnow() - last_dt).total_seconds() / 3600
            if age_hours < 24:
                logger.info(f"Rosters are fresh ({age_hours:.1f}h old). Skipping refresh.")
                should_refresh = False
        except Exception:
            pass

    if should_refresh:
        logger.info("Refreshing IPL rosters from ESPNcricinfo...")
        try:
            summary = refresh_all_rosters(use_scraping=True)
            logger.info(f"Rosters refreshed: {summary}")
        except Exception as e:
            logger.warning(f"Live scraping failed ({e}). Using fallback squads.")
            refresh_all_rosters(use_scraping=False)


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(predict.router,  prefix="/predict",  tags=["Predict"])
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
app.include_router(history.router,  prefix="/history",  tags=["History"])
app.include_router(teams.router,    prefix="/teams",    tags=["Teams & Rosters"])


@app.get("/")
def root():
    return {"message": "IPL Score Predictor API v2 is live 🏏"}


@app.get("/health")
def health():
    return {"status": "ok"}
