"""
backend/tests/test_api.py
--------------------------
Basic smoke tests for the FastAPI endpoints.
Run with: pytest backend/tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Patch external services before importing app
with patch("app.services.model_service.load_model"), \
     patch("app.services.db_service.get_client"):
    from main import app

client = TestClient(app)

SAMPLE_PAYLOAD = {
    "batting_team": "Mumbai Indians",
    "bowling_team": "Chennai Super Kings",
    "venue": "Wankhede Stadium",
    "playing_12": [
        "Rohit Sharma", "Ishan Kishan", "Suryakumar Yadav",
        "Hardik Pandya", "Tilak Varma", "Tim David",
        "Jasprit Bumrah", "MS Dhoni", "Ravindra Jadeja",
        "Ruturaj Gaikwad", "Devon Conway"
    ],
    "batting_team_players": [
        "Rohit Sharma", "Ishan Kishan", "Suryakumar Yadav",
        "Hardik Pandya", "Tilak Varma", "Tim David"
    ],
    "bowling_team_players": [
        "MS Dhoni", "Ravindra Jadeja", "Ruturaj Gaikwad",
        "Devon Conway", "Jasprit Bumrah"
    ],
    "pitch_type": "Flat",
    "pitch_hardness": 7,
    "dew_factor": False,
    "toss_winner": "Mumbai Indians",
    "toss_decision": "Bat",
    "match_time": "Evening (D/N)",
    "season": 2024,
}


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "IPL" in res.json()["message"]


@patch("app.services.db_service.save_prediction", return_value="test-uuid-1234")
@patch("app.services.model_service._model", None)  # Force heuristic mode
def test_predict(mock_save):
    res = client.post("/predict/", json=SAMPLE_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert "predicted_score" in data
    assert "confidence_range" in data
    assert "phase_breakdown" in data
    assert "prediction_id" in data
    assert 100 <= data["predicted_score"] <= 250  # sanity range


@patch("app.services.db_service.save_feedback")
def test_feedback(mock_fb):
    res = client.post("/feedback/", json={
        "prediction_id": "test-uuid-1234",
        "actual_score": 178,
        "user_rating": 4,
        "comments": "Pretty close!",
    })
    assert res.status_code == 200
    assert res.json()["status"] == "success"


@patch("app.services.db_service.get_prediction_history", return_value=[])
def test_history_empty(mock_hist):
    res = client.get("/history/")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["avg_abs_error_runs"] is None
