"""
cricket_data_service.py
------------------------
Fetches live IPL team rosters and recent match data from ESPNcricinfo.
Stores results in Supabase so the frontend always shows current squads.

Sources:
  - ESPNcricinfo squad pages (scraping) for player rosters
  - Cricsheet.org for historical + new match ball-by-ball data
  - ESPN Cricinfo unofficial JSON endpoints for recent match metadata
"""

import os
import re
import logging
import datetime
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup
from supabase import create_client

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ── IPL team IDs on ESPNcricinfo ──────────────────────────────────────────────
# These are stable numeric IDs used in ESPNcricinfo URLs
IPL_TEAMS = {
    "Mumbai Indians": {
        "id": "664409",
        "short": "MI",
        "home_ground": "Wankhede Stadium",
    },
    "Chennai Super Kings": {
        "id": "333613",
        "short": "CSK",
        "home_ground": "MA Chidambaram Stadium",
    },
    "Royal Challengers Bengaluru": {
        "id": "335974",
        "short": "RCB",
        "home_ground": "M Chinnaswamy Stadium",
    },
    "Kolkata Knight Riders": {
        "id": "333616",
        "short": "KKR",
        "home_ground": "Eden Gardens",
    },
    "Delhi Capitals": {
        "id": "333614",
        "short": "DC",
        "home_ground": "Arun Jaitley Stadium",
    },
    "Rajasthan Royals": {
        "id": "335973",
        "short": "RR",
        "home_ground": "Sawai Mansingh Stadium",
    },
    "Sunrisers Hyderabad": {
        "id": "ball",
        "short": "SRH",
        "home_ground": "Rajiv Gandhi International Stadium",
    },
    "Punjab Kings": {
        "id": "335977",
        "short": "PBKS",
        "home_ground": "Punjab Cricket Association Stadium",
    },
    "Lucknow Super Giants": {
        "id": "1321777",
        "short": "LSG",
        "home_ground": "BRSABV Ekana Cricket Stadium",
    },
    "Gujarat Titans": {
        "id": "1321778",
        "short": "GT",
        "home_ground": "Narendra Modi Stadium",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ── Supabase helpers ──────────────────────────────────────────────────────────

def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Roster fetching ───────────────────────────────────────────────────────────

def fetch_team_squad(team_name: str, team_id: str) -> list[dict]:
    """
    Scrape the current IPL squad for a team from ESPNcricinfo.
    Returns list of player dicts with name, role, country, etc.
    """
    url = f"https://www.espncricinfo.com/team/{team_name.lower().replace(' ', '-')}-{team_id}/squad"
    players = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # ESPNcricinfo squad page — player cards
        # Look for player name elements in squad listing
        player_cards = soup.find_all("a", href=re.compile(r"/cricketers/"))

        seen = set()
        for card in player_cards:
            name_el = card.find("p") or card
            name = name_el.get_text(strip=True)
            href = card.get("href", "")

            # Extract player ID from URL e.g. /cricketers/rohit-sharma-34102
            pid_match = re.search(r"-(\d+)$", href)
            player_id = pid_match.group(1) if pid_match else None

            if name and len(name) > 3 and name not in seen and player_id:
                seen.add(name)

                # Try to get role from nearby element
                role_el = card.find_next("p", class_=re.compile(r"role|position", re.I))
                role = role_el.get_text(strip=True) if role_el else "Unknown"

                players.append({
                    "name": name,
                    "espncricinfo_id": player_id,
                    "team_name": team_name,
                    "role": role,
                    "is_active": True,
                })

        logger.info(f"Fetched {len(players)} players for {team_name} from ESPNcricinfo")

    except Exception as e:
        logger.warning(f"ESPNcricinfo scrape failed for {team_name}: {e}. Using fallback.")
        players = _fallback_squad(team_name)

    return players


def _fallback_squad(team_name: str) -> list[dict]:
    """
    Hardcoded 2025 IPL squads as a reliable fallback when scraping fails.
    Update this after each IPL auction.
    Last updated: IPL 2025 auction
    """
    SQUADS = {
        "Mumbai Indians": [
            {"name": "Rohit Sharma",      "role": "Batter",         "country": "India"},
            {"name": "Ishan Kishan",      "role": "WK-Batter",      "country": "India"},
            {"name": "Suryakumar Yadav",  "role": "Batter",         "country": "India"},
            {"name": "Hardik Pandya",     "role": "All-rounder",    "country": "India"},
            {"name": "Tilak Varma",       "role": "Batter",         "country": "India"},
            {"name": "Naman Dhir",        "role": "All-rounder",    "country": "India"},
            {"name": "Tim David",         "role": "Batter",         "country": "Singapore"},
            {"name": "Jasprit Bumrah",    "role": "Bowler",         "country": "India"},
            {"name": "Trent Boult",       "role": "Bowler",         "country": "New Zealand"},
            {"name": "Gerald Coetzee",    "role": "Bowler",         "country": "South Africa"},
            {"name": "Piyush Chawla",     "role": "Bowler",         "country": "India"},
            {"name": "Akash Madhwal",     "role": "Bowler",         "country": "India"},
        ],
        "Chennai Super Kings": [
            {"name": "MS Dhoni",          "role": "WK-Batter",      "country": "India"},
            {"name": "Ruturaj Gaikwad",   "role": "Batter",         "country": "India"},
            {"name": "Devon Conway",      "role": "WK-Batter",      "country": "New Zealand"},
            {"name": "Daryl Mitchell",    "role": "All-rounder",    "country": "New Zealand"},
            {"name": "Shivam Dube",       "role": "All-rounder",    "country": "India"},
            {"name": "Ravindra Jadeja",   "role": "All-rounder",    "country": "India"},
            {"name": "Moeen Ali",         "role": "All-rounder",    "country": "England"},
            {"name": "Mitchell Santner",  "role": "All-rounder",    "country": "New Zealand"},
            {"name": "Deepak Chahar",     "role": "Bowler",         "country": "India"},
            {"name": "Tushar Deshpande",  "role": "Bowler",         "country": "India"},
            {"name": "Matheesha Pathirana","role": "Bowler",        "country": "Sri Lanka"},
            {"name": "Mukesh Choudhary",  "role": "Bowler",         "country": "India"},
        ],
        "Royal Challengers Bengaluru": [
            {"name": "Faf du Plessis",    "role": "Batter",         "country": "South Africa"},
            {"name": "Virat Kohli",       "role": "Batter",         "country": "India"},
            {"name": "Glenn Maxwell",     "role": "All-rounder",    "country": "Australia"},
            {"name": "Dinesh Karthik",    "role": "WK-Batter",      "country": "India"},
            {"name": "Cameron Green",     "role": "All-rounder",    "country": "Australia"},
            {"name": "Mahipal Lomror",    "role": "All-rounder",    "country": "India"},
            {"name": "Suyash Prabhudessai","role": "All-rounder",  "country": "India"},
            {"name": "Mohammed Siraj",    "role": "Bowler",         "country": "India"},
            {"name": "Josh Hazlewood",    "role": "Bowler",         "country": "Australia"},
            {"name": "Wanindu Hasaranga", "role": "All-rounder",   "country": "Sri Lanka"},
            {"name": "Karn Sharma",       "role": "Bowler",         "country": "India"},
            {"name": "Reece Topley",      "role": "Bowler",         "country": "England"},
        ],
        "Kolkata Knight Riders": [
            {"name": "Shreyas Iyer",      "role": "Batter",         "country": "India"},
            {"name": "Phil Salt",         "role": "WK-Batter",      "country": "England"},
            {"name": "Sunil Narine",      "role": "All-rounder",    "country": "West Indies"},
            {"name": "Andre Russell",     "role": "All-rounder",    "country": "West Indies"},
            {"name": "Rinku Singh",       "role": "Batter",         "country": "India"},
            {"name": "Angkrish Raghuvanshi","role": "Batter",       "country": "India"},
            {"name": "Venkatesh Iyer",    "role": "All-rounder",    "country": "India"},
            {"name": "Mitchell Starc",    "role": "Bowler",         "country": "Australia"},
            {"name": "Pat Cummins",       "role": "All-rounder",    "country": "Australia"},
            {"name": "Varun Chakravarthy","role": "Bowler",         "country": "India"},
            {"name": "Harshit Rana",      "role": "Bowler",         "country": "India"},
            {"name": "Ramandeep Singh",   "role": "All-rounder",    "country": "India"},
        ],
        "Delhi Capitals": [
            {"name": "David Warner",      "role": "Batter",         "country": "Australia"},
            {"name": "Prithvi Shaw",      "role": "Batter",         "country": "India"},
            {"name": "Rishabh Pant",      "role": "WK-Batter",      "country": "India"},
            {"name": "Mitchell Marsh",    "role": "All-rounder",    "country": "Australia"},
            {"name": "Axar Patel",        "role": "All-rounder",    "country": "India"},
            {"name": "Kuldeep Yadav",     "role": "Bowler",         "country": "India"},
            {"name": "Anrich Nortje",     "role": "Bowler",         "country": "South Africa"},
            {"name": "Khaleel Ahmed",     "role": "Bowler",         "country": "India"},
            {"name": "Tristan Stubbs",    "role": "Batter",         "country": "South Africa"},
            {"name": "Jake Fraser-McGurk","role": "Batter",        "country": "Australia"},
            {"name": "Mukesh Kumar",      "role": "Bowler",         "country": "India"},
            {"name": "Rasikh Dar",        "role": "Bowler",         "country": "India"},
        ],
        "Rajasthan Royals": [
            {"name": "Jos Buttler",       "role": "WK-Batter",      "country": "England"},
            {"name": "Yashasvi Jaiswal",  "role": "Batter",         "country": "India"},
            {"name": "Sanju Samson",      "role": "WK-Batter",      "country": "India"},
            {"name": "Joe Root",          "role": "Batter",         "country": "England"},
            {"name": "Shimron Hetmyer",   "role": "Batter",         "country": "West Indies"},
            {"name": "Ravichandran Ashwin","role": "All-rounder",   "country": "India"},
            {"name": "Yuzvendra Chahal",  "role": "Bowler",         "country": "India"},
            {"name": "Trent Boult",       "role": "Bowler",         "country": "New Zealand"},
            {"name": "Sandeep Sharma",    "role": "Bowler",         "country": "India"},
            {"name": "Dhruv Jurel",       "role": "WK-Batter",      "country": "India"},
            {"name": "Riyan Parag",       "role": "All-rounder",    "country": "India"},
            {"name": "Rovman Powell",     "role": "Batter",         "country": "West Indies"},
        ],
        "Sunrisers Hyderabad": [
            {"name": "Travis Head",       "role": "Batter",         "country": "Australia"},
            {"name": "Abhishek Sharma",   "role": "All-rounder",    "country": "India"},
            {"name": "Heinrich Klaasen",  "role": "WK-Batter",      "country": "South Africa"},
            {"name": "Aiden Markram",     "role": "All-rounder",    "country": "South Africa"},
            {"name": "Nitish Reddy",      "role": "All-rounder",    "country": "India"},
            {"name": "Pat Cummins",       "role": "All-rounder",    "country": "Australia"},
            {"name": "T Natarajan",       "role": "Bowler",         "country": "India"},
            {"name": "Bhuvneshwar Kumar", "role": "Bowler",         "country": "India"},
            {"name": "Jaydev Unadkat",    "role": "Bowler",         "country": "India"},
            {"name": "Shahbaz Ahmed",     "role": "All-rounder",    "country": "India"},
            {"name": "Marco Jansen",      "role": "All-rounder",    "country": "South Africa"},
            {"name": "Wanindu Hasaranga", "role": "All-rounder",   "country": "Sri Lanka"},
        ],
        "Punjab Kings": [
            {"name": "Shikhar Dhawan",    "role": "Batter",         "country": "India"},
            {"name": "Jonny Bairstow",    "role": "WK-Batter",      "country": "England"},
            {"name": "Liam Livingstone",  "role": "All-rounder",    "country": "England"},
            {"name": "Sam Curran",        "role": "All-rounder",    "country": "England"},
            {"name": "Shahrukh Khan",     "role": "Batter",         "country": "India"},
            {"name": "Kagiso Rabada",     "role": "Bowler",         "country": "South Africa"},
            {"name": "Arshdeep Singh",    "role": "Bowler",         "country": "India"},
            {"name": "Nathan Ellis",      "role": "Bowler",         "country": "Australia"},
            {"name": "Rahul Chahar",      "role": "Bowler",         "country": "India"},
            {"name": "Harpreet Brar",     "role": "All-rounder",    "country": "India"},
            {"name": "Atharva Taide",     "role": "Batter",         "country": "India"},
            {"name": "Prabhsimran Singh", "role": "WK-Batter",      "country": "India"},
        ],
        "Lucknow Super Giants": [
            {"name": "KL Rahul",          "role": "WK-Batter",      "country": "India"},
            {"name": "Quinton de Kock",   "role": "WK-Batter",      "country": "South Africa"},
            {"name": "Nicholas Pooran",   "role": "WK-Batter",      "country": "West Indies"},
            {"name": "Deepak Hooda",      "role": "All-rounder",    "country": "India"},
            {"name": "Marcus Stoinis",    "role": "All-rounder",    "country": "Australia"},
            {"name": "Kyle Mayers",       "role": "All-rounder",    "country": "West Indies"},
            {"name": "Krunal Pandya",     "role": "All-rounder",    "country": "India"},
            {"name": "Ravi Bishnoi",      "role": "Bowler",         "country": "India"},
            {"name": "Mohsin Khan",       "role": "Bowler",         "country": "India"},
            {"name": "Mayank Yadav",      "role": "Bowler",         "country": "India"},
            {"name": "Mark Wood",         "role": "Bowler",         "country": "England"},
            {"name": "Yudhvir Singh",     "role": "Bowler",         "country": "India"},
        ],
        "Gujarat Titans": [
            {"name": "Shubman Gill",      "role": "Batter",         "country": "India"},
            {"name": "Wriddhiman Saha",   "role": "WK-Batter",      "country": "India"},
            {"name": "David Miller",      "role": "Batter",         "country": "South Africa"},
            {"name": "Kane Williamson",   "role": "Batter",         "country": "New Zealand"},
            {"name": "Vijay Shankar",     "role": "All-rounder",    "country": "India"},
            {"name": "Rahul Tewatia",     "role": "All-rounder",    "country": "India"},
            {"name": "Rashid Khan",       "role": "All-rounder",    "country": "Afghanistan"},
            {"name": "Mohammed Shami",    "role": "Bowler",         "country": "India"},
            {"name": "Mohit Sharma",      "role": "Bowler",         "country": "India"},
            {"name": "Noor Ahmad",        "role": "Bowler",         "country": "Afghanistan"},
            {"name": "Sai Sudharsan",     "role": "Batter",         "country": "India"},
            {"name": "Azmatullah Omarzai","role": "All-rounder",    "country": "Afghanistan"},
        ],
    }
    squad = SQUADS.get(team_name, [])
    return [
        {**p, "team_name": team_name, "is_active": True, "espncricinfo_id": None}
        for p in squad
    ]


# ── Persist to Supabase ───────────────────────────────────────────────────────

def upsert_teams(db) -> None:
    """Insert/update all 10 IPL teams in the teams table."""
    rows = [
        {
            "name": name,
            "short_name": info["short"],
            "espncricinfo_id": info["id"],
            "home_ground": info["home_ground"],
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }
        for name, info in IPL_TEAMS.items()
    ]
    db.table("teams").upsert(rows, on_conflict="name").execute()
    logger.info(f"Upserted {len(rows)} teams")


def upsert_players(db, team_name: str, players: list[dict]) -> None:
    """Insert/update player records for a team."""
    if not players:
        return
    rows = [
        {
            "name": p["name"],
            "team_name": team_name,
            "role": p.get("role", "Unknown"),
            "country": p.get("country", "Unknown"),
            "espncricinfo_id": p.get("espncricinfo_id"),
            "is_active": True,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }
        for p in players
    ]
    # Mark all existing players for this team as inactive first
    db.table("players").update({"is_active": False}).eq("team_name", team_name).execute()
    # Then upsert current squad as active
    db.table("players").upsert(rows, on_conflict="name,team_name").execute()
    logger.info(f"Upserted {len(rows)} players for {team_name}")


# ── Main refresh entry point ──────────────────────────────────────────────────

def refresh_all_rosters(use_scraping: bool = True) -> dict:
    """
    Fetch and store current squads for all 10 IPL teams.
    Called on API startup and by GitHub Actions scheduled job.
    Returns a summary dict.
    """
    db = get_db()
    upsert_teams(db)

    summary = {}
    for team_name, info in IPL_TEAMS.items():
        try:
            if use_scraping:
                players = fetch_team_squad(team_name, info["id"])
            else:
                players = _fallback_squad(team_name)

            upsert_players(db, team_name, players)
            summary[team_name] = len(players)
            time.sleep(1)  # Be polite to ESPNcricinfo
        except Exception as e:
            logger.error(f"Failed to refresh roster for {team_name}: {e}")
            summary[team_name] = 0

    # Update last_refreshed metadata
    db.table("app_metadata").upsert({
        "key": "rosters_last_updated",
        "value": datetime.datetime.utcnow().isoformat(),
    }, on_conflict="key").execute()

    logger.info(f"Roster refresh complete: {summary}")
    return summary


# ── Query helpers (used by API routers) ──────────────────────────────────────

def get_all_teams() -> list[dict]:
    db = get_db()
    result = db.table("teams").select("*").order("name").execute()
    return result.data


def get_players_for_team(team_name: str) -> list[dict]:
    """Return current active players for a given team, ordered by role."""
    db = get_db()
    result = (
        db.table("players")
        .select("name, role, country, espncricinfo_id")
        .eq("team_name", team_name)
        .eq("is_active", True)
        .order("role")
        .execute()
    )
    return result.data


def get_rosters_last_updated() -> Optional[str]:
    """Return ISO timestamp of last roster refresh."""
    try:
        db = get_db()
        result = (
            db.table("app_metadata")
            .select("value")
            .eq("key", "rosters_last_updated")
            .single()
            .execute()
        )
        return result.data["value"] if result.data else None
    except Exception:
        return None
