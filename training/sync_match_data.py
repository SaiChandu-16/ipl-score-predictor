"""
training/sync_match_data.py
----------------------------
Downloads the latest IPL match data from Cricsheet.org and appends
new matches to the training dataset in Supabase.

Cricsheet updates their ZIP after every match.
This script is run by GitHub Actions after each IPL match day.

Usage:
    python training/sync_match_data.py
"""

import os
import io
import re
import csv
import zipfile
import logging
import datetime
import requests
from supabase import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# Cricsheet always serves the full IPL dataset at this URL
CRICSHEET_IPL_URL = "https://cricsheet.org/downloads/ipl_csv2.zip"

VENUE_MAP = {
    "Wankhede Stadium, Mumbai":                          "Wankhede Stadium",
    "M Chinnaswamy Stadium, Bengaluru":                  "M Chinnaswamy Stadium",
    "Eden Gardens, Kolkata":                             "Eden Gardens",
    "MA Chidambaram Stadium, Chepauk, Chennai":          "MA Chidambaram Stadium",
    "Arun Jaitley Stadium, Delhi":                       "Arun Jaitley Stadium",
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad": "Rajiv Gandhi International Stadium",
    "Punjab Cricket Association IS Bindra Stadium, Mohali": "Punjab Cricket Association Stadium",
    "Sawai Mansingh Stadium, Jaipur":                    "Sawai Mansingh Stadium",
    "Narendra Modi Stadium, Ahmedabad":                  "Narendra Modi Stadium",
    "BRSABV Ekana Cricket Stadium, Lucknow":             "BRSABV Ekana Cricket Stadium",
}


def download_cricsheet_zip() -> zipfile.ZipFile:
    """Download the full IPL CSV2 dataset from Cricsheet."""
    logger.info(f"Downloading IPL data from {CRICSHEET_IPL_URL} ...")
    resp = requests.get(CRICSHEET_IPL_URL, timeout=120)
    resp.raise_for_status()
    logger.info(f"Downloaded {len(resp.content) / 1024:.0f} KB")
    return zipfile.ZipFile(io.BytesIO(resp.content))


def get_existing_match_ids(db) -> set:
    """Fetch all match IDs already stored in Supabase to avoid re-inserting."""
    result = db.table("match_data").select("cricsheet_match_id").execute()
    return {row["cricsheet_match_id"] for row in result.data}


def parse_match_file(content: str) -> dict | None:
    """
    Parse a single Cricsheet CSV2 match file.
    Returns a flat dict of match-level features for training.
    """
    lines = content.splitlines()
    info = {}
    ball_rows = []

    for line in lines:
        parts = line.split(",")
        if not parts:
            continue
        if parts[0] == "info" and len(parts) >= 3:
            key, val = parts[1], parts[2]
            if key in info:
                # Handle repeated keys (e.g. player_of_match)
                existing = info[key]
                if isinstance(existing, list):
                    existing.append(val)
                else:
                    info[key] = [existing, val]
            else:
                info[key] = val
        elif parts[0] == "ball" and len(parts) >= 13:
            ball_rows.append(parts)

    if not ball_rows or info.get("match_type") != "T20":
        return None

    # Build innings 1 score
    inn1_runs = 0
    inn1_wickets = 0
    batting_team = None
    bowling_team = None

    for row in ball_rows:
        try:
            inning = row[2]
            if inning != "1":
                continue
            if batting_team is None:
                batting_team = row[3]
                bowling_team = row[4]
            inn1_runs += int(row[12])  # runs_total
            # Count wickets (non-empty wicket column)
            if len(row) > 13 and row[13].strip() not in ("", "0"):
                inn1_wickets += 1
        except (IndexError, ValueError):
            continue

    if not batting_team or inn1_runs < 50:
        return None

    teams = info.get("team", [])
    if isinstance(teams, str):
        teams = [teams]

    venue_raw = info.get("venue", "")
    venue = VENUE_MAP.get(venue_raw, venue_raw.split(",")[0].strip())

    toss_winner   = info.get("toss_winner", "")
    toss_decision = info.get("toss_decision", "bat").capitalize()
    season_raw    = info.get("season", "0")
    season        = int(str(season_raw).split("/")[0])
    match_id      = info.get("match_id", info.get("matchid", ""))

    # Date
    date_str = info.get("date", "")
    try:
        match_date = datetime.date.fromisoformat(date_str).isoformat()
    except Exception:
        match_date = None

    return {
        "cricsheet_match_id": str(match_id),
        "season": season,
        "match_date": match_date,
        "venue": venue,
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "toss_winner": toss_winner,
        "toss_decision": toss_decision,
        "innings_score": inn1_runs,
        "innings_wickets": inn1_wickets,
        # Placeholder columns — enriched later or kept as defaults
        "pitch_type": "Flat",
        "pitch_hardness": 7,
        "dew_factor": False,
        "match_time": "Evening",
        "num_batting_players": 6,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }


def sync(dry_run: bool = False) -> dict:
    """Main sync function. Downloads Cricsheet, parses, inserts new matches."""
    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    existing_ids = get_existing_match_ids(db)
    logger.info(f"Already have {len(existing_ids)} matches in Supabase")

    zf = download_cricsheet_zip()
    csv_files = [n for n in zf.namelist() if n.endswith(".csv") and "_info" not in n]
    logger.info(f"Found {len(csv_files)} match files in ZIP")

    new_rows = []
    skipped = 0
    errors = 0

    for fname in csv_files:
        try:
            content = zf.read(fname).decode("utf-8", errors="replace")
            row = parse_match_file(content)
            if row is None:
                skipped += 1
                continue
            if row["cricsheet_match_id"] in existing_ids:
                skipped += 1
                continue
            new_rows.append(row)
        except Exception as e:
            logger.warning(f"Error parsing {fname}: {e}")
            errors += 1

    logger.info(f"New matches to insert: {len(new_rows)} | Skipped: {skipped} | Errors: {errors}")

    if not dry_run and new_rows:
        # Insert in batches of 100
        batch_size = 100
        for i in range(0, len(new_rows), batch_size):
            batch = new_rows[i : i + batch_size]
            db.table("match_data").insert(batch).execute()
            logger.info(f"Inserted batch {i // batch_size + 1} ({len(batch)} rows)")

        # Update sync metadata
        db.table("app_metadata").upsert({
            "key": "match_data_last_synced",
            "value": datetime.datetime.utcnow().isoformat(),
        }, on_conflict="key").execute()

    return {
        "new_matches_inserted": len(new_rows),
        "skipped": skipped,
        "errors": errors,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Parse but don't insert")
    args = parser.parse_args()
    result = sync(dry_run=args.dry_run)
    logger.info(f"Sync result: {result}")
