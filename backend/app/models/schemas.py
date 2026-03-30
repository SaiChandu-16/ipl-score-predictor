from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class PitchType(str, Enum):
    dry          = "Dry"
    grassy       = "Grassy"
    dusty        = "Dusty"
    flat         = "Flat"
    spin_friendly = "Spin Friendly"
    pace_friendly = "Pace Friendly"


class TossDecision(str, Enum):
    bat   = "Bat"
    field = "Field"


class MatchInput(BaseModel):
    batting_team:          str
    bowling_team:          str
    venue:                 str
    playing_12:            List[str] = Field(..., min_length=11, max_length=12)
    batting_team_players:  List[str]
    bowling_team_players:  List[str]
    pitch_type:            PitchType
    pitch_hardness:        int = Field(..., ge=1, le=10)
    dew_factor:            bool = False
    toss_winner:           str
    toss_decision:         TossDecision
    match_time:            str = "Evening"
    season:                int

    model_config = {"use_enum_values": True}   # ✅ enums serialise as plain strings


class PredictionResponse(BaseModel):
    prediction_id:    str
    predicted_score:  int
    confidence_range: dict
    phase_breakdown:  dict
    model_version:    str


class FeedbackInput(BaseModel):
    prediction_id: str
    actual_score:  int
    user_rating:   Optional[int] = Field(None, ge=1, le=5)
    comments:      Optional[str] = None