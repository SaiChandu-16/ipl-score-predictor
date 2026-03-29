"""
seed.py  —  Run this ONCE locally to populate Supabase with IPL squads.

Usage:
    pip install supabase
    python seed.py

Fill in your SUPABASE_URL and SUPABASE_KEY below before running.
"""

import datetime
from supabase import create_client

# ── FILL THESE IN ─────────────────────────────────────────────────────────────
SUPABASE_URL = "https://qjqzognzwelffyysuphj.supabase.co"
# SUPABASE_URL  # ← paste from Supabase → Settings → API
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqcXpvZ256d2VsZmZ5eXN1cGhqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2OTA4MjAsImV4cCI6MjA5MDI2NjgyMH0.LcwR0FuDa03-a_1KC0wiIQrymEqNEbAM8q5f_mhaDhI"                              # ← paste anon key
# ─────────────────────────────────────────────────────────────────────────────

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

SQUADS = {
    "Mumbai Indians": [
        {"name": "Rohit Sharma",       "role": "Batter",      "country": "India"},
        {"name": "Ishan Kishan",       "role": "WK-Batter",   "country": "India"},
        {"name": "Suryakumar Yadav",   "role": "Batter",      "country": "India"},
        {"name": "Hardik Pandya",      "role": "All-rounder", "country": "India"},
        {"name": "Tilak Varma",        "role": "Batter",      "country": "India"},
        {"name": "Naman Dhir",         "role": "All-rounder", "country": "India"},
        {"name": "Tim David",          "role": "Batter",      "country": "Singapore"},
        {"name": "Jasprit Bumrah",     "role": "Bowler",      "country": "India"},
        {"name": "Trent Boult",        "role": "Bowler",      "country": "New Zealand"},
        {"name": "Gerald Coetzee",     "role": "Bowler",      "country": "South Africa"},
        {"name": "Piyush Chawla",      "role": "Bowler",      "country": "India"},
        {"name": "Akash Madhwal",      "role": "Bowler",      "country": "India"},
    ],
    "Chennai Super Kings": [
        {"name": "MS Dhoni",           "role": "WK-Batter",   "country": "India"},
        {"name": "Ruturaj Gaikwad",    "role": "Batter",      "country": "India"},
        {"name": "Devon Conway",       "role": "WK-Batter",   "country": "New Zealand"},
        {"name": "Daryl Mitchell",     "role": "All-rounder", "country": "New Zealand"},
        {"name": "Shivam Dube",        "role": "All-rounder", "country": "India"},
        {"name": "Ravindra Jadeja",    "role": "All-rounder", "country": "India"},
        {"name": "Moeen Ali",          "role": "All-rounder", "country": "England"},
        {"name": "Mitchell Santner",   "role": "All-rounder", "country": "New Zealand"},
        {"name": "Deepak Chahar",      "role": "Bowler",      "country": "India"},
        {"name": "Tushar Deshpande",   "role": "Bowler",      "country": "India"},
        {"name": "Matheesha Pathirana","role": "Bowler",      "country": "Sri Lanka"},
        {"name": "Mukesh Choudhary",   "role": "Bowler",      "country": "India"},
    ],
    "Royal Challengers Bengaluru": [
        {"name": "Faf du Plessis",     "role": "Batter",      "country": "South Africa"},
        {"name": "Virat Kohli",        "role": "Batter",      "country": "India"},
        {"name": "Glenn Maxwell",      "role": "All-rounder", "country": "Australia"},
        {"name": "Dinesh Karthik",     "role": "WK-Batter",   "country": "India"},
        {"name": "Cameron Green",      "role": "All-rounder", "country": "Australia"},
        {"name": "Mahipal Lomror",     "role": "All-rounder", "country": "India"},
        {"name": "Mohammed Siraj",     "role": "Bowler",      "country": "India"},
        {"name": "Josh Hazlewood",     "role": "Bowler",      "country": "Australia"},
        {"name": "Wanindu Hasaranga",  "role": "All-rounder", "country": "Sri Lanka"},
        {"name": "Karn Sharma",        "role": "Bowler",      "country": "India"},
        {"name": "Reece Topley",       "role": "Bowler",      "country": "England"},
        {"name": "Suyash Prabhudessai","role": "All-rounder", "country": "India"},
    ],
    "Kolkata Knight Riders": [
        {"name": "Shreyas Iyer",       "role": "Batter",      "country": "India"},
        {"name": "Phil Salt",          "role": "WK-Batter",   "country": "England"},
        {"name": "Sunil Narine",       "role": "All-rounder", "country": "West Indies"},
        {"name": "Andre Russell",      "role": "All-rounder", "country": "West Indies"},
        {"name": "Rinku Singh",        "role": "Batter",      "country": "India"},
        {"name": "Venkatesh Iyer",     "role": "All-rounder", "country": "India"},
        {"name": "Angkrish Raghuvanshi","role": "Batter",     "country": "India"},
        {"name": "Mitchell Starc",     "role": "Bowler",      "country": "Australia"},
        {"name": "Pat Cummins",        "role": "All-rounder", "country": "Australia"},
        {"name": "Varun Chakravarthy", "role": "Bowler",      "country": "India"},
        {"name": "Harshit Rana",       "role": "Bowler",      "country": "India"},
        {"name": "Ramandeep Singh",    "role": "All-rounder", "country": "India"},
    ],
    "Delhi Capitals": [
        {"name": "David Warner",       "role": "Batter",      "country": "Australia"},
        {"name": "Prithvi Shaw",       "role": "Batter",      "country": "India"},
        {"name": "Rishabh Pant",       "role": "WK-Batter",   "country": "India"},
        {"name": "Mitchell Marsh",     "role": "All-rounder", "country": "Australia"},
        {"name": "Axar Patel",         "role": "All-rounder", "country": "India"},
        {"name": "Kuldeep Yadav",      "role": "Bowler",      "country": "India"},
        {"name": "Anrich Nortje",      "role": "Bowler",      "country": "South Africa"},
        {"name": "Khaleel Ahmed",      "role": "Bowler",      "country": "India"},
        {"name": "Tristan Stubbs",     "role": "Batter",      "country": "South Africa"},
        {"name": "Jake Fraser-McGurk", "role": "Batter",      "country": "Australia"},
        {"name": "Mukesh Kumar",       "role": "Bowler",      "country": "India"},
        {"name": "Rasikh Dar",         "role": "Bowler",      "country": "India"},
    ],
    "Rajasthan Royals": [
        {"name": "Jos Buttler",        "role": "WK-Batter",   "country": "England"},
        {"name": "Yashasvi Jaiswal",   "role": "Batter",      "country": "India"},
        {"name": "Sanju Samson",       "role": "WK-Batter",   "country": "India"},
        {"name": "Joe Root",           "role": "Batter",      "country": "England"},
        {"name": "Shimron Hetmyer",    "role": "Batter",      "country": "West Indies"},
        {"name": "Ravichandran Ashwin","role": "All-rounder", "country": "India"},
        {"name": "Yuzvendra Chahal",   "role": "Bowler",      "country": "India"},
        {"name": "Trent Boult",        "role": "Bowler",      "country": "New Zealand"},
        {"name": "Sandeep Sharma",     "role": "Bowler",      "country": "India"},
        {"name": "Dhruv Jurel",        "role": "WK-Batter",   "country": "India"},
        {"name": "Riyan Parag",        "role": "All-rounder", "country": "India"},
        {"name": "Rovman Powell",      "role": "Batter",      "country": "West Indies"},
    ],
    "Sunrisers Hyderabad": [
        {"name": "Travis Head",        "role": "Batter",      "country": "Australia"},
        {"name": "Abhishek Sharma",    "role": "All-rounder", "country": "India"},
        {"name": "Heinrich Klaasen",   "role": "WK-Batter",   "country": "South Africa"},
        {"name": "Aiden Markram",      "role": "All-rounder", "country": "South Africa"},
        {"name": "Nitish Reddy",       "role": "All-rounder", "country": "India"},
        {"name": "Pat Cummins",        "role": "All-rounder", "country": "Australia"},
        {"name": "T Natarajan",        "role": "Bowler",      "country": "India"},
        {"name": "Bhuvneshwar Kumar",  "role": "Bowler",      "country": "India"},
        {"name": "Jaydev Unadkat",     "role": "Bowler",      "country": "India"},
        {"name": "Shahbaz Ahmed",      "role": "All-rounder", "country": "India"},
        {"name": "Marco Jansen",       "role": "All-rounder", "country": "South Africa"},
        {"name": "Wanindu Hasaranga",  "role": "All-rounder", "country": "Sri Lanka"},
    ],
    "Punjab Kings": [
        {"name": "Shikhar Dhawan",     "role": "Batter",      "country": "India"},
        {"name": "Jonny Bairstow",     "role": "WK-Batter",   "country": "England"},
        {"name": "Liam Livingstone",   "role": "All-rounder", "country": "England"},
        {"name": "Sam Curran",         "role": "All-rounder", "country": "England"},
        {"name": "Shahrukh Khan",      "role": "Batter",      "country": "India"},
        {"name": "Kagiso Rabada",      "role": "Bowler",      "country": "South Africa"},
        {"name": "Arshdeep Singh",     "role": "Bowler",      "country": "India"},
        {"name": "Nathan Ellis",       "role": "Bowler",      "country": "Australia"},
        {"name": "Rahul Chahar",       "role": "Bowler",      "country": "India"},
        {"name": "Harpreet Brar",      "role": "All-rounder", "country": "India"},
        {"name": "Atharva Taide",      "role": "Batter",      "country": "India"},
        {"name": "Prabhsimran Singh",  "role": "WK-Batter",   "country": "India"},
    ],
    "Lucknow Super Giants": [
        {"name": "KL Rahul",           "role": "WK-Batter",   "country": "India"},
        {"name": "Quinton de Kock",    "role": "WK-Batter",   "country": "South Africa"},
        {"name": "Nicholas Pooran",    "role": "WK-Batter",   "country": "West Indies"},
        {"name": "Deepak Hooda",       "role": "All-rounder", "country": "India"},
        {"name": "Marcus Stoinis",     "role": "All-rounder", "country": "Australia"},
        {"name": "Kyle Mayers",        "role": "All-rounder", "country": "West Indies"},
        {"name": "Krunal Pandya",      "role": "All-rounder", "country": "India"},
        {"name": "Ravi Bishnoi",       "role": "Bowler",      "country": "India"},
        {"name": "Mohsin Khan",        "role": "Bowler",      "country": "India"},
        {"name": "Mayank Yadav",       "role": "Bowler",      "country": "India"},
        {"name": "Mark Wood",          "role": "Bowler",      "country": "England"},
        {"name": "Yudhvir Singh",      "role": "Bowler",      "country": "India"},
    ],
    "Gujarat Titans": [
        {"name": "Shubman Gill",       "role": "Batter",      "country": "India"},
        {"name": "Wriddhiman Saha",    "role": "WK-Batter",   "country": "India"},
        {"name": "David Miller",       "role": "Batter",      "country": "South Africa"},
        {"name": "Kane Williamson",    "role": "Batter",      "country": "New Zealand"},
        {"name": "Vijay Shankar",      "role": "All-rounder", "country": "India"},
        {"name": "Rahul Tewatia",      "role": "All-rounder", "country": "India"},
        {"name": "Rashid Khan",        "role": "All-rounder", "country": "Afghanistan"},
        {"name": "Mohammed Shami",     "role": "Bowler",      "country": "India"},
        {"name": "Mohit Sharma",       "role": "Bowler",      "country": "India"},
        {"name": "Noor Ahmad",         "role": "Bowler",      "country": "Afghanistan"},
        {"name": "Sai Sudharsan",      "role": "Batter",      "country": "India"},
        {"name": "Azmatullah Omarzai", "role": "All-rounder", "country": "Afghanistan"},
    ],
}


def seed():
    print("🔌 Connecting to Supabase...")
    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    # ── 1. Upsert teams ────────────────────────────────────────────────────────
    print("\n📋 Seeding teams table...")
    team_rows = [
        {
            "name":            name,
            "short_name":      info["short"],
            "espncricinfo_id": None,
            "home_ground":     info["home"],
            "updated_at":      datetime.datetime.utcnow().isoformat(),
        }
        for name, info in IPL_TEAMS.items()
    ]
    db.table("teams").upsert(team_rows, on_conflict="name").execute()
    print(f"  ✅ {len(team_rows)} teams inserted")

    # ── 2. Upsert players per team ─────────────────────────────────────────────
    print("\n👥 Seeding players table...")
    total = 0
    for team_name, players in SQUADS.items():
        # Mark all existing players for this team inactive first
        db.table("players").update({"is_active": False}).eq("team_name", team_name).execute()

        rows = [
            {
                "name":             p["name"],
                "team_name":        team_name,
                "role":             p["role"],
                "country":          p["country"],
                "espncricinfo_id":  None,
                "is_active":        True,
                "updated_at":       datetime.datetime.utcnow().isoformat(),
            }
            for p in players
        ]
        db.table("players").upsert(rows, on_conflict="name,team_name").execute()
        total += len(rows)
        print(f"  ✅ {team_name}: {len(rows)} players")

    # ── 3. Update metadata ─────────────────────────────────────────────────────
    db.table("app_metadata").upsert(
        {"key": "rosters_last_updated", "value": datetime.datetime.utcnow().isoformat()},
        on_conflict="key"
    ).execute()

    print(f"\n🎉 Done! {len(team_rows)} teams and {total} players seeded into Supabase.")
    print("👉 Now refresh your Streamlit app — squads should load correctly.\n")


if __name__ == "__main__":
    if "your-project" in SUPABASE_URL:
        print("❌ Please fill in SUPABASE_URL and SUPABASE_KEY at the top of this file!")
        exit(1)
    seed()