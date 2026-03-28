"""
training/prepare_data.py
------------------------
Download and parse Cricsheet IPL ball-by-ball data into a flat
match-level CSV suitable for training.

Usage:
    1. Download IPL data from https://cricsheet.org/downloads/ipl_csv2.zip
    2. Unzip into data/raw/
    3. Run: python training/prepare_data.py
    4. Output: data/ipl_matches.csv
"""

import os
import glob
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_DIR = "data/raw"
OUTPUT_PATH = "data/ipl_matches.csv"

# Venue name normalization (Cricsheet names → our names)
VENUE_MAP = {
    "Wankhede Stadium, Mumbai": "Wankhede Stadium",
    "M Chinnaswamy Stadium, Bengaluru": "M Chinnaswamy Stadium",
    "Eden Gardens, Kolkata": "Eden Gardens",
    "MA Chidambaram Stadium, Chepauk, Chennai": "MA Chidambaram Stadium",
    "Arun Jaitley Stadium, Delhi": "Arun Jaitley Stadium",
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad": "Rajiv Gandhi International Stadium",
    "Punjab Cricket Association IS Bindra Stadium, Mohali": "Punjab Cricket Association Stadium",
    "Sawai Mansingh Stadium, Jaipur": "Sawai Mansingh Stadium",
    "Narendra Modi Stadium, Ahmedabad": "Narendra Modi Stadium",
}


def parse_match_csv(filepath: str) -> dict:
    """
    Parse a single Cricsheet match CSV file into a match-level dict.
    Cricsheet CSV2 format has an info section at the top.
    """
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()

        info = {}
        ball_rows = []
        in_balls = False

        for line in lines:
            parts = line.strip().split(",")
            if parts[0] == "info":
                key = parts[1] if len(parts) > 1 else ""
                val = parts[2] if len(parts) > 2 else ""
                info[key] = val
            elif parts[0] == "ball":
                in_balls = True
            elif in_balls:
                ball_rows.append(parts)

        if not ball_rows:
            return None

        df = pd.DataFrame(ball_rows, columns=[
            "type", "match_id", "inning", "batting_team", "bowling_team",
            "over", "ball", "batter", "bowler", "non_striker", "runs_batter",
            "runs_extras", "runs_total", "wickets", "extras_type", "other_fielder"
        ] + ["extra"] * 10)  # extra columns for safety

        # Innings 1 total
        inn1 = df[df["inning"] == "1"]
        if inn1.empty:
            return None

        innings_score = inn1["runs_total"].astype(float).sum()
        batting_team = inn1["batting_team"].iloc[0]

        venue_raw = info.get("venue", "Unknown")
        venue = VENUE_MAP.get(venue_raw, venue_raw.split(",")[0])

        toss_winner = info.get("toss_winner", "")
        toss_decision = info.get("toss_decision", "").capitalize()
        season = int(info.get("season", "0").split("/")[0])

        return {
            "venue": venue,
            "batting_team": batting_team,
            "toss_winner": toss_winner,
            "toss_decision": toss_decision,
            "season": season,
            "innings_score": int(innings_score),
            # These need to be filled manually or from a separate pitch DB
            "pitch_type": "Flat",       # placeholder
            "pitch_hardness": 7,        # placeholder
            "dew_factor": 0,            # placeholder
            "match_time": "Evening",    # placeholder
            "num_batting_players": 6,   # placeholder
        }
    except Exception as e:
        logger.warning(f"Failed to parse {filepath}: {e}")
        return None


def prepare():
    files = glob.glob(os.path.join(RAW_DIR, "*.csv"))
    logger.info(f"Found {len(files)} match files in {RAW_DIR}")

    records = []
    for f in files:
        row = parse_match_csv(f)
        if row:
            records.append(row)

    if not records:
        logger.error("No valid match records found. Check your data directory.")
        return

    df = pd.DataFrame(records)
    df = df.sort_values("season").reset_index(drop=True)
    df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"✅ Saved {len(df)} matches to {OUTPUT_PATH}")
    logger.info(df.describe())


if __name__ == "__main__":
    prepare()
