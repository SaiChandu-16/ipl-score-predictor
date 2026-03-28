from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class PitchType(str, Enum):
    dry = "Dry"
    grassy = "Grassy"
    dusty = "Dusty"
    flat = "Flat"
    spin_friendly = "Spin Friendly"
    pace_friendly = "Pace Friendly"

class TossDecision(str, Enum):
    bat = "Bat"
    field = "Field"

class MatchInput(BaseModel):
    batting_team: str = Field(..., example="Mumbai Indians")
    bowling_team: str = Field(..., example="Chennai Super Kings")
    venue: str = Field(..., example="Wankhede Stadium")
    playing_12: List[str] = Field(..., min_items=11, max_items=12, example=["Rohit Sharma", "Ishan Kishan"])
    batting_team_players: List[str] = Field(..., description="Players from batting team")
    bowling_team_players: List[str] = Field(..., description="Players from bowling team")
    pitch_type: PitchType = Field(..., example="Flat")
    pitch_hardness: int = Field(..., ge=1, le=10, description="1=very soft, 10=very hard", example=7)
    dew_factor: bool = Field(default=False, description="Is dew expected?")
    toss_winner: str = Field(..., example="Mumbai Indians")
    toss_decision: TossDecision = Field(..., example="Bat")
    match_time: str = Field(default="Evening", example="Evening")  # Day / Evening
    season: int = Field(..., example=2024)

class PredictionResponse(BaseModel):
    prediction_id: str
    predicted_score: int
    confidence_range: dict  # {"low": int, "high": int}
    phase_breakdown: dict   # {"powerplay": int, "middle": int, "death": int}
    model_version: str

class FeedbackInput(BaseModel):
    prediction_id: str
    actual_score: int
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="1-5 rating of prediction quality")
    comments: Optional[str] = None
