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

"""
cricket_data_service.py
------------------------
Fetches live IPL team rosters and stores them in Supabase.
Fallback squads updated to IPL 2026 (post Dec 2025 auction).
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

IPL_TEAMS = {
    "Mumbai Indians":                {"id": "664409",  "short": "MI",   "home_ground": "Wankhede Stadium"},
    "Chennai Super Kings":           {"id": "333613",  "short": "CSK",  "home_ground": "MA Chidambaram Stadium"},
    "Royal Challengers Bengaluru":   {"id": "335974",  "short": "RCB",  "home_ground": "M Chinnaswamy Stadium"},
    "Kolkata Knight Riders":         {"id": "333616",  "short": "KKR",  "home_ground": "Eden Gardens"},
    "Delhi Capitals":                {"id": "333614",  "short": "DC",   "home_ground": "Arun Jaitley Stadium"},
    "Rajasthan Royals":              {"id": "335973",  "short": "RR",   "home_ground": "Sawai Mansingh Stadium"},
    "Sunrisers Hyderabad":           {"id": "ball",    "short": "SRH",  "home_ground": "Rajiv Gandhi International Stadium"},
    "Punjab Kings":                  {"id": "335977",  "short": "PBKS", "home_ground": "Punjab Cricket Association Stadium"},
    "Lucknow Super Giants":          {"id": "1321777", "short": "LSG",  "home_ground": "BRSABV Ekana Cricket Stadium"},
    "Gujarat Titans":                {"id": "1321778", "short": "GT",   "home_ground": "Narendra Modi Stadium"},
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_team_squad(team_name: str, team_id: str) -> list[dict]:
    url = f"https://www.espncricinfo.com/team/{team_name.lower().replace(' ', '-')}-{team_id}/squad"
    players = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        player_cards = soup.find_all("a", href=re.compile(r"/cricketers/"))
        seen = set()
        for card in player_cards:
            name_el = card.find("p") or card
            name = name_el.get_text(strip=True)
            href = card.get("href", "")
            pid_match = re.search(r"-(\d+)$", href)
            player_id = pid_match.group(1) if pid_match else None
            if name and len(name) > 3 and name not in seen and player_id:
                seen.add(name)
                role_el = card.find_next("p", class_=re.compile(r"role|position", re.I))
                role = role_el.get_text(strip=True) if role_el else "Unknown"
                players.append({"name": name, "espncricinfo_id": player_id,
                                 "team_name": team_name, "role": role, "is_active": True})
        logger.info(f"Fetched {len(players)} players for {team_name}")
    except Exception as e:
        logger.warning(f"ESPNcricinfo scrape failed for {team_name}: {e}. Using fallback.")
        players = _fallback_squad(team_name)
    return players


def _fallback_squad(team_name: str) -> list[dict]:
    """
    IPL 2026 squads — updated after December 2025 auction.
    Key changes: Sanju Samson→CSK, Cameron Green→KKR (₹25.2cr record),
    Matheesha Pathirana→KKR, Venkatesh Iyer→RCB, Liam Livingstone→SRH,
    Rishabh Pant→LSG (captain), Jos Buttler→RR, RCB defending champions.
    """
    SQUADS = {
        "Chennai Super Kings": [
            {"name": "Ruturaj Gaikwad",    "role": "Batter",      "country": "India"},
            {"name": "MS Dhoni",           "role": "WK-Batter",   "country": "India"},
            {"name": "Sanju Samson",       "role": "WK-Batter",   "country": "India"},
            {"name": "Ayush Mhatre",       "role": "Batter",      "country": "India"},
            {"name": "Dewald Brevis",      "role": "Batter",      "country": "South Africa"},
            {"name": "Shivam Dube",        "role": "All-rounder", "country": "India"},
            {"name": "Kartik Sharma",      "role": "All-rounder", "country": "India"},
            {"name": "Prashant Veer",      "role": "All-rounder", "country": "India"},
            {"name": "Sarfaraz Khan",      "role": "Batter",      "country": "India"},
            {"name": "Urvil Patel",        "role": "WK-Batter",   "country": "India"},
            {"name": "Matthew Short",      "role": "All-rounder", "country": "Australia"},
            {"name": "Jamie Overton",      "role": "All-rounder", "country": "England"},
            {"name": "Ramakrishna Ghosh",  "role": "All-rounder", "country": "India"},
            {"name": "Shreyas Gopal",      "role": "All-rounder", "country": "India"},
            {"name": "Akeal Hosein",       "role": "All-rounder", "country": "West Indies"},
            {"name": "Noor Ahmad",         "role": "Bowler",      "country": "Afghanistan"},
            {"name": "Khaleel Ahmed",      "role": "Bowler",      "country": "India"},
            {"name": "Mukesh Choudhary",   "role": "Bowler",      "country": "India"},
            {"name": "Anshul Kamboj",      "role": "Bowler",      "country": "India"},
            {"name": "Nathan Ellis",       "role": "Bowler",      "country": "Australia"},
            {"name": "Matt Henry",         "role": "Bowler",      "country": "New Zealand"},
            {"name": "Rahul Chahar",       "role": "Bowler",      "country": "India"},
        ],
        "Mumbai Indians": [
            {"name": "Hardik Pandya",      "role": "All-rounder", "country": "India"},
            {"name": "Rohit Sharma",       "role": "Batter",      "country": "India"},
            {"name": "Suryakumar Yadav",   "role": "Batter",      "country": "India"},
            {"name": "Jasprit Bumrah",     "role": "Bowler",      "country": "India"},
            {"name": "Quinton de Kock",    "role": "WK-Batter",   "country": "South Africa"},
            {"name": "Ishan Kishan",       "role": "WK-Batter",   "country": "India"},
            {"name": "Tilak Varma",        "role": "Batter",      "country": "India"},
            {"name": "Naman Dhir",         "role": "All-rounder", "country": "India"},
            {"name": "Tim David",          "role": "Batter",      "country": "Singapore"},
            {"name": "Trent Boult",        "role": "Bowler",      "country": "New Zealand"},
            {"name": "Gerald Coetzee",     "role": "Bowler",      "country": "South Africa"},
            {"name": "Piyush Chawla",      "role": "Bowler",      "country": "India"},
            {"name": "Akash Madhwal",      "role": "Bowler",      "country": "India"},
            {"name": "Deepak Chahar",      "role": "Bowler",      "country": "India"},
            {"name": "Reece Topley",       "role": "Bowler",      "country": "England"},
            {"name": "Robin Minz",         "role": "WK-Batter",   "country": "India"},
            {"name": "Raj Angad Bawa",     "role": "All-rounder", "country": "India"},
        ],
        "Royal Challengers Bengaluru": [
            {"name": "Virat Kohli",        "role": "Batter",      "country": "India"},
            {"name": "Rajat Patidar",      "role": "Batter",      "country": "India"},
            {"name": "Phil Salt",          "role": "WK-Batter",   "country": "England"},
            {"name": "Venkatesh Iyer",     "role": "All-rounder", "country": "India"},
            {"name": "Jitesh Sharma",      "role": "WK-Batter",   "country": "India"},
            {"name": "Jordan Cox",         "role": "WK-Batter",   "country": "England"},
            {"name": "Devdutt Padikkal",   "role": "Batter",      "country": "India"},
            {"name": "Krunal Pandya",      "role": "All-rounder", "country": "India"},
            {"name": "Romario Shepherd",   "role": "All-rounder", "country": "West Indies"},
            {"name": "Jacob Bethell",      "role": "All-rounder", "country": "England"},
            {"name": "Swapnil Singh",      "role": "All-rounder", "country": "India"},
            {"name": "Vicky Ostwal",       "role": "Bowler",      "country": "India"},
            {"name": "Bhuvneshwar Kumar",  "role": "Bowler",      "country": "India"},
            {"name": "Josh Hazlewood",     "role": "Bowler",      "country": "Australia"},
            {"name": "Yash Dayal",         "role": "Bowler",      "country": "India"},
            {"name": "Mangesh Yadav",      "role": "Bowler",      "country": "India"},
            {"name": "Nuwan Thushara",     "role": "Bowler",      "country": "Sri Lanka"},
            {"name": "Rasikh Dar",         "role": "Bowler",      "country": "India"},
            {"name": "Jacob Duffy",        "role": "Bowler",      "country": "New Zealand"},
        ],
        "Kolkata Knight Riders": [
            {"name": "Ajinkya Rahane",      "role": "Batter",      "country": "India"},
            {"name": "Cameron Green",       "role": "All-rounder", "country": "Australia"},
            {"name": "Matheesha Pathirana", "role": "Bowler",      "country": "Sri Lanka"},
            {"name": "Sunil Narine",        "role": "All-rounder", "country": "West Indies"},
            {"name": "Andre Russell",       "role": "All-rounder", "country": "West Indies"},
            {"name": "Rinku Singh",         "role": "Batter",      "country": "India"},
            {"name": "Angkrish Raghuvanshi","role": "Batter",      "country": "India"},
            {"name": "Ramandeep Singh",     "role": "All-rounder", "country": "India"},
            {"name": "Varun Chakravarthy",  "role": "Bowler",      "country": "India"},
            {"name": "Harshit Rana",        "role": "Bowler",      "country": "India"},
            {"name": "Spencer Johnson",     "role": "Bowler",      "country": "Australia"},
            {"name": "Blessing Muzarabani", "role": "Bowler",      "country": "Zimbabwe"},
            {"name": "Rovman Powell",       "role": "Batter",      "country": "West Indies"},
            {"name": "Luvnith Sisodia",     "role": "WK-Batter",   "country": "India"},
            {"name": "Moeen Ali",           "role": "All-rounder", "country": "England"},
        ],
        "Delhi Capitals": [
            {"name": "Axar Patel",          "role": "All-rounder", "country": "India"},
            {"name": "KL Rahul",            "role": "WK-Batter",   "country": "India"},
            {"name": "Faf du Plessis",      "role": "Batter",      "country": "South Africa"},
            {"name": "Jake Fraser-McGurk",  "role": "Batter",      "country": "Australia"},
            {"name": "Tristan Stubbs",      "role": "Batter",      "country": "South Africa"},
            {"name": "Abishek Porel",       "role": "WK-Batter",   "country": "India"},
            {"name": "Prithvi Shaw",        "role": "Batter",      "country": "India"},
            {"name": "Karun Nair",          "role": "Batter",      "country": "India"},
            {"name": "Ashutosh Sharma",     "role": "All-rounder", "country": "India"},
            {"name": "Kuldeep Yadav",       "role": "Bowler",      "country": "India"},
            {"name": "Mitchell Starc",      "role": "Bowler",      "country": "Australia"},
            {"name": "Mukesh Kumar",        "role": "Bowler",      "country": "India"},
            {"name": "T Natarajan",         "role": "Bowler",      "country": "India"},
            {"name": "Mohit Sharma",        "role": "Bowler",      "country": "India"},
            {"name": "Vipraj Nigam",        "role": "Bowler",      "country": "India"},
        ],
        "Rajasthan Royals": [
            {"name": "Riyan Parag",         "role": "All-rounder", "country": "India"},
            {"name": "Jos Buttler",         "role": "WK-Batter",   "country": "England"},
            {"name": "Yashasvi Jaiswal",    "role": "Batter",      "country": "India"},
            {"name": "Shimron Hetmyer",     "role": "Batter",      "country": "West Indies"},
            {"name": "Dhruv Jurel",         "role": "WK-Batter",   "country": "India"},
            {"name": "Vaibhav Suryavanshi", "role": "Batter",      "country": "India"},
            {"name": "Nitish Rana",         "role": "Batter",      "country": "India"},
            {"name": "Shubham Dubey",       "role": "All-rounder", "country": "India"},
            {"name": "Ravichandran Ashwin", "role": "All-rounder", "country": "India"},
            {"name": "Wanindu Hasaranga",   "role": "All-rounder", "country": "Sri Lanka"},
            {"name": "Yuzvendra Chahal",    "role": "Bowler",      "country": "India"},
            {"name": "Trent Boult",         "role": "Bowler",      "country": "New Zealand"},
            {"name": "Sandeep Sharma",      "role": "Bowler",      "country": "India"},
            {"name": "Akash Deep",          "role": "Bowler",      "country": "India"},
            {"name": "Maheesh Theekshana",  "role": "Bowler",      "country": "Sri Lanka"},
        ],
        "Sunrisers Hyderabad": [
            {"name": "Pat Cummins",         "role": "All-rounder", "country": "Australia"},
            {"name": "Travis Head",         "role": "Batter",      "country": "Australia"},
            {"name": "Abhishek Sharma",     "role": "All-rounder", "country": "India"},
            {"name": "Heinrich Klaasen",    "role": "WK-Batter",   "country": "South Africa"},
            {"name": "Liam Livingstone",    "role": "All-rounder", "country": "England"},
            {"name": "Aiden Markram",       "role": "All-rounder", "country": "South Africa"},
            {"name": "Nitish Reddy",        "role": "All-rounder", "country": "India"},
            {"name": "Marco Jansen",        "role": "All-rounder", "country": "South Africa"},
            {"name": "Shahbaz Ahmed",       "role": "All-rounder", "country": "India"},
            {"name": "Kamindu Mendis",      "role": "All-rounder", "country": "Sri Lanka"},
            {"name": "Adam Zampa",          "role": "Bowler",      "country": "Australia"},
            {"name": "Harshal Patel",       "role": "Bowler",      "country": "India"},
            {"name": "T Natarajan",         "role": "Bowler",      "country": "India"},
            {"name": "Brydon Carse",        "role": "Bowler",      "country": "England"},
            {"name": "Zeeshan Ansari",      "role": "Bowler",      "country": "India"},
        ],
        "Punjab Kings": [
            {"name": "Shreyas Iyer",        "role": "Batter",      "country": "India"},
            {"name": "Prabhsimran Singh",   "role": "WK-Batter",   "country": "India"},
            {"name": "Priyansh Arya",       "role": "Batter",      "country": "India"},
            {"name": "Nehal Wadhera",       "role": "Batter",      "country": "India"},
            {"name": "Shashank Singh",      "role": "Batter",      "country": "India"},
            {"name": "Musheer Khan",        "role": "Batter",      "country": "India"},
            {"name": "Marcus Stoinis",      "role": "All-rounder", "country": "Australia"},
            {"name": "Azmatullah Omarzai",  "role": "All-rounder", "country": "Afghanistan"},
            {"name": "Cooper Connolly",     "role": "All-rounder", "country": "Australia"},
            {"name": "Harpreet Brar",       "role": "All-rounder", "country": "India"},
            {"name": "Arshdeep Singh",      "role": "Bowler",      "country": "India"},
            {"name": "Lockie Ferguson",     "role": "Bowler",      "country": "New Zealand"},
            {"name": "Yuzvendra Chahal",    "role": "Bowler",      "country": "India"},
            {"name": "Ben Dwarshuis",       "role": "Bowler",      "country": "Australia"},
            {"name": "Praveen Dubey",       "role": "Bowler",      "country": "India"},
            {"name": "Vidhwath Kaverappa",  "role": "Bowler",      "country": "India"},
        ],
        "Lucknow Super Giants": [
            {"name": "Rishabh Pant",        "role": "WK-Batter",   "country": "India"},
            {"name": "Mitchell Marsh",      "role": "All-rounder", "country": "Australia"},
            {"name": "Nicholas Pooran",     "role": "WK-Batter",   "country": "West Indies"},
            {"name": "Josh Inglis",         "role": "WK-Batter",   "country": "Australia"},
            {"name": "Ayush Badoni",        "role": "Batter",      "country": "India"},
            {"name": "Abdul Samad",         "role": "Batter",      "country": "India"},
            {"name": "Wanindu Hasaranga",   "role": "All-rounder", "country": "Sri Lanka"},
            {"name": "Arshin Kulkarni",     "role": "All-rounder", "country": "India"},
            {"name": "Arjun Tendulkar",     "role": "All-rounder", "country": "India"},
            {"name": "Mohammed Shami",      "role": "Bowler",      "country": "India"},
            {"name": "Mayank Yadav",        "role": "Bowler",      "country": "India"},
            {"name": "Avesh Khan",          "role": "Bowler",      "country": "India"},
            {"name": "Mohsin Khan",         "role": "Bowler",      "country": "India"},
            {"name": "Anrich Nortje",       "role": "Bowler",      "country": "South Africa"},
            {"name": "Digvesh Singh",       "role": "Bowler",      "country": "India"},
            {"name": "M Siddharth",         "role": "Bowler",      "country": "India"},
        ],
        "Gujarat Titans": [
            {"name": "Shubman Gill",        "role": "Batter",      "country": "India"},
            {"name": "Rashid Khan",         "role": "All-rounder", "country": "Afghanistan"},
            {"name": "Kagiso Rabada",       "role": "Bowler",      "country": "South Africa"},
            {"name": "Mohammed Siraj",      "role": "Bowler",      "country": "India"},
            {"name": "David Miller",        "role": "Batter",      "country": "South Africa"},
            {"name": "Wriddhiman Saha",     "role": "WK-Batter",   "country": "India"},
            {"name": "Sai Sudharsan",       "role": "Batter",      "country": "India"},
            {"name": "Kane Williamson",     "role": "Batter",      "country": "New Zealand"},
            {"name": "Rahul Tewatia",       "role": "All-rounder", "country": "India"},
            {"name": "Vijay Shankar",       "role": "All-rounder", "country": "India"},
            {"name": "Shahrukh Khan",       "role": "Batter",      "country": "India"},
            {"name": "Prasidh Krishna",     "role": "Bowler",      "country": "India"},
            {"name": "Mohit Sharma",        "role": "Bowler",      "country": "India"},
            {"name": "Noor Ahmad",          "role": "Bowler",      "country": "Afghanistan"},
            {"name": "Manav Suthar",        "role": "Bowler",      "country": "India"},
            {"name": "Ishant Sharma",       "role": "Bowler",      "country": "India"},
        ],
    }
    squad = SQUADS.get(team_name, [])
    return [
        {**p, "team_name": team_name, "is_active": True, "espncricinfo_id": None}
        for p in squad
    ]


# ── Supabase helpers ──────────────────────────────────────────────────────────

def upsert_teams(db) -> None:
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
    db.table("players").update({"is_active": False}).eq("team_name", team_name).execute()
    db.table("players").upsert(rows, on_conflict="name,team_name").execute()
    logger.info(f"Upserted {len(rows)} players for {team_name}")


def refresh_all_rosters(use_scraping: bool = True) -> dict:
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
            if use_scraping:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Failed to refresh {team_name}: {e}")
            summary[team_name] = 0

    db.table("app_metadata").upsert(
        {"key": "rosters_last_updated", "value": datetime.datetime.utcnow().isoformat()},
        on_conflict="key"
    ).execute()
    logger.info(f"Roster refresh complete: {summary}")
    return summary


def get_all_teams() -> list[dict]:
    db = get_db()
    return db.table("teams").select("*").order("name").execute().data


def get_players_for_team(team_name: str) -> list[dict]:
    db = get_db()
    return (
        db.table("players")
        .select("name, role, country, espncricinfo_id")
        .eq("team_name", team_name)
        .eq("is_active", True)
        .order("role")
        .execute()
        .data
    )


def get_rosters_last_updated() -> Optional[str]:
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