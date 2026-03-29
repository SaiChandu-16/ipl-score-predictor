"""
app/routers/admin.py
---------------------
Protected admin endpoints for updating squads and data
without needing a local seed script.

Protected by ADMIN_SECRET env var — set this in Render → Environment.
Call via: POST /admin/seed-squads
          with header: X-Admin-Secret: your_secret_here
"""

import os
import datetime
import logging
from fastapi import APIRouter, HTTPException, Header
from app.services.db_service import get_client

router = APIRouter()
logger = logging.getLogger(__name__)

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")

# ── IPL 2026 Squads ───────────────────────────────────────────────────────────
IPL_TEAMS = {
    "Mumbai Indians":                {"short": "MI",   "home": "Wankhede Stadium"},
    "Chennai Super Kings":           {"short": "CSK",  "home": "MA Chidambaram Stadium"},
    "Royal Challengers Bengaluru":   {"short": "RCB",  "home": "M Chinnaswamy Stadium"},
    "Kolkata Knight Riders":         {"short": "KKR",  "home": "Eden Gardens"},
    "Delhi Capitals":                {"short": "DC",   "home": "Arun Jaitley Stadium"},
    "Rajasthan Royals":              {"short": "RR",   "home": "Sawai Mansingh Stadium"},
    "Sunrisers Hyderabad":           {"short": "SRH",  "home": "Rajiv Gandhi International Stadium"},
    "Punjab Kings":                  {"short": "PBKS", "home": "Punjab Cricket Association Stadium"},
    "Lucknow Super Giants":          {"short": "LSG",  "home": "BRSABV Ekana Cricket Stadium"},
    "Gujarat Titans":                {"short": "GT",   "home": "Narendra Modi Stadium"},
}

SQUADS_2026 = {
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
        {"name": "Zak Foulkes",        "role": "All-rounder", "country": "England"},
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
        {"name": "Luvnith Sisodia",     "role": "WK-Batter",  "country": "India"},
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
        {"name": "Vaibhav Suryavanshi","role": "Batter",       "country": "India"},
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
        {"name": "Harshal Patel",       "role": "Bowler",      "country": "India"},
        {"name": "T Natarajan",         "role": "Bowler",      "country": "India"},
        {"name": "Brydon Carse",        "role": "Bowler",      "country": "England"},
        {"name": "Adam Zampa",          "role": "Bowler",      "country": "Australia"},
        {"name": "Kamindu Mendis",      "role": "All-rounder", "country": "Sri Lanka"},
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


def _verify_secret(x_admin_secret: str):
    if not ADMIN_SECRET:
        raise HTTPException(
            status_code=500,
            detail="ADMIN_SECRET env var not set on server. Add it in Render → Environment."
        )
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret.")


@router.post("/seed-squads")
async def seed_squads(x_admin_secret: str = Header(...)):
    """
    Re-seed all 10 IPL 2026 squads into Supabase.

    Call with:
        curl -X POST https://your-api.onrender.com/admin/seed-squads \
             -H "x-admin-secret: YOUR_SECRET"

    Or use the Swagger UI at /docs — click Authorize and enter your secret.
    """
    _verify_secret(x_admin_secret)

    try:
        db = get_client()
        now = datetime.datetime.utcnow().isoformat()

        # 1. Upsert teams
        team_rows = [
            {"name": name, "short_name": info["short"],
             "home_ground": info["home"], "updated_at": now}
            for name, info in IPL_TEAMS.items()
        ]
        db.table("teams").upsert(team_rows, on_conflict="name").execute()

        # 2. Upsert players per team
        total = 0
        summary = {}
        for team_name, players in SQUADS_2026.items():
            db.table("players").update({"is_active": False}).eq("team_name", team_name).execute()
            rows = [
                {"name": p["name"], "team_name": team_name, "role": p["role"],
                 "country": p["country"], "is_active": True, "updated_at": now}
                for p in players
            ]
            db.table("players").upsert(rows, on_conflict="name,team_name").execute()
            summary[team_name] = len(rows)
            total += len(rows)

        # 3. Update metadata
        db.table("app_metadata").upsert(
            {"key": "rosters_last_updated", "value": now},
            on_conflict="key"
        ).execute()

        return {
            "status": "✅ success",
            "message": "IPL 2026 squads seeded successfully",
            "teams": len(SQUADS_2026),
            "total_players": total,
            "breakdown": summary,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deactivate-player")
async def deactivate_player(
    team_name: str,
    player_name: str,
    x_admin_secret: str = Header(...),
):
    """Remove a player from a team (e.g. injury replacement)."""
    _verify_secret(x_admin_secret)
    try:
        db = get_client()
        db.table("players").update({"is_active": False})\
            .eq("team_name", team_name)\
            .eq("name", player_name)\
            .execute()
        return {"status": "✅ success", "message": f"{player_name} deactivated from {team_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-player")
async def add_player(
    team_name: str,
    player_name: str,
    role: str,
    country: str = "India",
    x_admin_secret: str = Header(...),
):
    """Add a new player to a team (e.g. replacement signing)."""
    _verify_secret(x_admin_secret)
    try:
        db = get_client()
        db.table("players").upsert(
            {"name": player_name, "team_name": team_name, "role": role,
             "country": country, "is_active": True,
             "updated_at": datetime.datetime.utcnow().isoformat()},
            on_conflict="name,team_name"
        ).execute()
        return {"status": "✅ success", "message": f"{player_name} added to {team_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))