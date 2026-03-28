import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
try:
    API_URL = st.secrets["API_URL"]
except Exception:
    API_URL = os.getenv("API_URL", "https://your-api.onrender.com")

st.set_page_config(
    page_title="IPL Score Predictor 🏏",
    page_icon="🏏",
    layout="wide",
)

# ── API health check with wake-up logic ───────────────────────────────────────

def check_api_awake() -> bool:
    """
    Ping /health. If it responds, API is warm.
    If it times out, it's cold-starting — show a user-friendly wait message.
    """
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False

def wait_for_api():
    """Show a warm-up banner and poll until the API wakes up (max 90s)."""
    placeholder = st.empty()
    for attempt in range(18):   # 18 × 5s = 90s max
        if check_api_awake():
            placeholder.empty()
            return True
        placeholder.warning(
            f"⏳ **API is waking up** (free tier cold start) — "
            f"please wait... {attempt * 5}s elapsed. "
            f"This happens once after ~15 min of inactivity."
        )
        import time
        time.sleep(5)
    placeholder.error(
        "❌ API did not respond after 90 seconds. "
        "Check your Render dashboard or try refreshing the page."
    )
    return False

# ── Data fetchers (cached) ────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_teams():
    """Returns ({team_name: meta}, last_updated_str)"""
    try:
        resp = requests.get(f"{API_URL}/teams/", timeout=20)
        resp.raise_for_status()
        data = resp.json()
        teams = {t["name"]: t for t in data["teams"]}
        return teams, data.get("rosters_last_updated")
    except Exception:
        return _default_teams(), None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_players(team_name: str) -> list:
    try:
        resp = requests.get(
            f"{API_URL}/teams/{requests.utils.quote(team_name)}/players",
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json().get("players", [])
    except Exception:
        return []


def _default_teams() -> dict:
    names = [
        "Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bengaluru",
        "Kolkata Knight Riders", "Delhi Capitals", "Rajasthan Royals",
        "Sunrisers Hyderabad", "Punjab Kings", "Lucknow Super Giants", "Gujarat Titans",
    ]
    return {n: {"name": n, "short_name": n[:3].upper(), "home_ground": ""} for n in names}


VENUES = [
    "Wankhede Stadium", "M Chinnaswamy Stadium", "Eden Gardens",
    "MA Chidambaram Stadium", "Arun Jaitley Stadium",
    "Rajiv Gandhi International Stadium", "Punjab Cricket Association Stadium",
    "Sawai Mansingh Stadium", "Narendra Modi Stadium",
    "BRSABV Ekana Cricket Stadium",
]

ROLE_EMOJI = {
    "Batter": "🏏", "WK-Batter": "🧤",
    "All-rounder": "⚡", "Bowler": "🎳", "Unknown": "❓",
}

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏏 IPL Score Predictor")
st.caption("Predict innings scores using live IPL rosters, pitch conditions, and toss result.")

# ── API Wake-up check (runs once per session) ─────────────────────────────────
if "api_ready" not in st.session_state:
    st.session_state["api_ready"] = False

if not st.session_state["api_ready"]:
    with st.spinner("Connecting to API..."):
        if check_api_awake():
            st.session_state["api_ready"] = True
        else:
            # API is cold — show the wait banner and poll
            awake = wait_for_api()
            st.session_state["api_ready"] = awake
            if awake:
                st.cache_data.clear()   # Clear any stale cached failures
                st.rerun()

if not st.session_state["api_ready"]:
    st.stop()   # Don't render the rest of the page if API never woke

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Predict", "📋 History & Accuracy", "👥 Team Squads", "📖 How it Works"
])

# ═══════════════════════════════════════════════
# TAB 1 — PREDICT
# ═══════════════════════════════════════════════
with tab1:
    with st.spinner("Loading live IPL team data..."):
        teams_data, last_updated = fetch_teams()

    team_names = sorted(teams_data.keys())

    if last_updated:
        try:
            dt = datetime.fromisoformat(last_updated)
            st.caption(f"📡 Rosters last updated: {dt.strftime('%d %b %Y, %H:%M UTC')}")
        except Exception:
            pass

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏟️ Match Info")
        batting_team = st.selectbox("Batting Team", team_names, key="bat_team")
        bowling_team = st.selectbox(
            "Bowling Team",
            [t for t in team_names if t != batting_team],
            key="bowl_team",
        )
        home_ground = teams_data.get(batting_team, {}).get("home_ground", "")
        default_venue_idx = VENUES.index(home_ground) if home_ground in VENUES else 0
        venue = st.selectbox("Venue", VENUES, index=default_venue_idx)
        season = st.selectbox("Season", list(range(2026, 2007, -1)), index=0)
        match_time = st.radio("Match Time", ["Evening (D/N)", "Day"], horizontal=True)

    with col2:
        st.subheader("🌿 Pitch Report")
        pitch_type = st.selectbox(
            "Pitch Type",
            ["Flat", "Dry", "Dusty", "Grassy", "Spin Friendly", "Pace Friendly"],
        )
        pitch_hardness = st.slider("Pitch Hardness", 1, 10, 7,
            help="1 = very soft/crumbly, 10 = very hard")
        dew_factor = st.toggle("🌫️ Dew Expected?", value=False)
        if dew_factor:
            st.info("Dew typically helps the chasing team.")

    st.divider()
    st.subheader("🎲 Toss")
    col3, col4 = st.columns(2)
    with col3:
        toss_winner = st.selectbox("Toss Winner", [batting_team, bowling_team])
    with col4:
        toss_decision = st.radio("Elected to", ["Bat", "Field"], horizontal=True)

    st.divider()
    st.subheader("👥 Select Playing 12")
    st.caption("Players loaded from live IPL rosters.")

    with st.spinner(f"Loading {batting_team} squad..."):
        batting_players_all = fetch_players(batting_team)
    with st.spinner(f"Loading {bowling_team} squad..."):
        bowling_players_all = fetch_players(bowling_team)

    def player_names(players): return [p["name"] for p in players]

    col5, col6 = st.columns(2)

    with col5:
        st.markdown(f"**{batting_team}**")
        if batting_players_all:
            bat_roles = {}
            for p in batting_players_all:
                bat_roles.setdefault(p.get("role", "Unknown"), []).append(p["name"])
            st.caption(" · ".join(f"{ROLE_EMOJI.get(r,'❓')} {r}: {len(ps)}" for r, ps in bat_roles.items()))
            batting_selected = st.multiselect(
                f"Select {batting_team} players",
                options=player_names(batting_players_all),
                default=player_names(batting_players_all)[:6],
                max_selections=7, key="bat_players",
            )
        else:
            st.warning(f"Could not load {batting_team} squad.")
            batting_selected = st.multiselect(f"Enter {batting_team} players", options=[], key="bat_players")

    with col6:
        st.markdown(f"**{bowling_team}**")
        if bowling_players_all:
            bowl_roles = {}
            for p in bowling_players_all:
                bowl_roles.setdefault(p.get("role", "Unknown"), []).append(p["name"])
            st.caption(" · ".join(f"{ROLE_EMOJI.get(r,'❓')} {r}: {len(ps)}" for r, ps in bowl_roles.items()))
            available_bowl = [p["name"] for p in bowling_players_all if p["name"] not in batting_selected]
            bowling_selected = st.multiselect(
                f"Select {bowling_team} players",
                options=available_bowl,
                default=available_bowl[:5],
                max_selections=6, key="bowl_players",
            )
        else:
            st.warning(f"Could not load {bowling_team} squad.")
            bowling_selected = st.multiselect(f"Enter {bowling_team} players", options=[], key="bowl_players")

    playing_12 = batting_selected + bowling_selected
    total = len(playing_12)
    color = "green" if total >= 11 else "orange" if total >= 9 else "red"
    st.markdown(f"**Total selected:** :{color}[{total} / 12 players]")

    st.divider()
    predict_btn = st.button("🚀 Predict Score", type="primary", use_container_width=True)

    if predict_btn:
        if len(playing_12) < 11:
            st.error(f"Please select at least 11 players total (currently {len(playing_12)}).")
        else:
            payload = {
                "batting_team": batting_team, "bowling_team": bowling_team,
                "venue": venue, "playing_12": playing_12,
                "batting_team_players": batting_selected,
                "bowling_team_players": bowling_selected,
                "pitch_type": pitch_type, "pitch_hardness": pitch_hardness,
                "dew_factor": dew_factor, "toss_winner": toss_winner,
                "toss_decision": toss_decision, "match_time": match_time, "season": season,
            }
            with st.spinner("Computing prediction..."):
                try:
                    res = requests.post(f"{API_URL}/predict/", json=payload, timeout=30)
                    res.raise_for_status()
                    data = res.json()
                    st.session_state["last_prediction_id"]   = data["prediction_id"]
                    st.session_state["last_predicted_score"] = data["predicted_score"]

                    st.success("✅ Prediction ready!")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("🏏 Predicted Score", f"{data['predicted_score']} runs")
                    m2.metric("📉 Low",  f"{data['confidence_range']['low']} runs")
                    m3.metric("📈 High", f"{data['confidence_range']['high']} runs")
                    m4.metric("🤖 Model", data["model_version"])

                    st.subheader("📊 Phase Breakdown")
                    phases = data["phase_breakdown"]
                    phase_df = pd.DataFrame({
                        "Phase": ["Powerplay (1–6)", "Middle Overs (7–15)", "Death Overs (16–20)"],
                        "Predicted Runs": [phases["powerplay"], phases["middle_overs"], phases["death_overs"]],
                    })
                    st.bar_chart(phase_df.set_index("Phase"))

                except requests.exceptions.ConnectionError:
                    st.error("❌ API is unreachable. Click the button below to wake it up.")
                    if st.button("🔄 Wake up API"):
                        st.session_state["api_ready"] = False
                        st.rerun()
                except Exception as e:
                    st.error(f"Prediction error: {e}")

    # ── Feedback ──────────────────────────────────────────────────────────────
    if "last_prediction_id" in st.session_state:
        st.divider()
        st.subheader("✅ Submit Actual Score (after the match)")
        with st.form("feedback_form"):
            actual_score = st.number_input("Actual Score", min_value=0, max_value=350, step=1)
            user_rating  = st.slider("Rate this prediction (1=very off, 5=spot on)", 1, 5, 3)
            comments     = st.text_input("Comments (optional)")
            submit_fb    = st.form_submit_button("📤 Submit Feedback")
        if submit_fb:
            try:
                fb_res = requests.post(f"{API_URL}/feedback/", json={
                    "prediction_id": st.session_state["last_prediction_id"],
                    "actual_score": actual_score, "user_rating": user_rating, "comments": comments,
                }, timeout=15)
                fb_res.raise_for_status()
                error = abs(st.session_state["last_predicted_score"] - actual_score)
                st.success(f"Thank you! Prediction was off by {error} runs 🏏")
            except Exception as e:
                st.error(f"Feedback error: {e}")

    with st.expander("🔄 Force roster refresh"):
        if st.button("Refresh Rosters Now"):
            try:
                requests.post(f"{API_URL}/teams/refresh", timeout=10)
                st.cache_data.clear()
                st.success("Refresh triggered! Reload in ~30 seconds.")
            except Exception as e:
                st.error(f"Could not trigger refresh: {e}")

# ═══════════════════════════════════════════════
# TAB 2 — HISTORY
# ═══════════════════════════════════════════════
with tab2:
    st.subheader("📋 Past Predictions & Accuracy")
    if st.button("🔄 Refresh"):
        st.rerun()
    try:
        hist_res = requests.get(f"{API_URL}/history/", params={"limit": 50}, timeout=15)
        hist_res.raise_for_status()
        hist = hist_res.json()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Predictions", hist["total"])
        c2.metric("With Actual Scores", hist["labeled_count"])
        c3.metric("Avg Error (runs)", hist["avg_abs_error_runs"] or "—")
        records = hist["records"]
        if records:
            df = pd.DataFrame([{
                "Date": r["created_at"][:10],
                "Batting Team": r["inputs"].get("batting_team", "—"),
                "Venue": r["inputs"].get("venue", "—"),
                "Predicted": r["predicted_score"],
                "Actual": r.get("actual_score") or "—",
                "Error": abs(r["predicted_score"] - r["actual_score"]) if r.get("actual_score") else "—",
                "⭐": r.get("user_rating") or "—",
            } for r in records])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No predictions yet. Make your first one!")
    except Exception as e:
        st.warning(f"Could not load history: {e}")

# ═══════════════════════════════════════════════
# TAB 3 — TEAM SQUADS
# ═══════════════════════════════════════════════
with tab3:
    st.subheader("👥 Current IPL Squads")
    teams_data_sq, last_updated_sq = fetch_teams()
    if last_updated_sq:
        try:
            dt = datetime.fromisoformat(last_updated_sq)
            st.info(f"📡 Last refreshed: {dt.strftime('%d %b %Y at %H:%M UTC')}")
        except Exception:
            pass

    selected_team = st.selectbox("Choose a team", sorted(teams_data_sq.keys()))
    if selected_team:
        with st.spinner(f"Loading {selected_team} squad..."):
            squad = fetch_players(selected_team)
        if squad:
            by_role = {}
            for p in squad:
                by_role.setdefault(p.get("role", "Unknown"), []).append(p)
            cols = st.columns(2)
            for i, (role, players) in enumerate(by_role.items()):
                with cols[i % 2]:
                    st.markdown(f"**{ROLE_EMOJI.get(role,'❓')} {role}s**")
                    for p in players:
                        flag = "🇮🇳" if p.get("country", "India") == "India" else "🌍"
                        st.markdown(f"&nbsp;&nbsp;{flag} {p['name']} <small style='color:gray'>({p.get('country','?')})</small>", unsafe_allow_html=True)
                    st.markdown("")
        else:
            st.warning("Could not load squad. API may be unavailable.")

# ═══════════════════════════════════════════════
# TAB 4 — HOW IT WORKS
# ═══════════════════════════════════════════════
with tab4:
    st.subheader("📖 How It Works")
    st.markdown("""
    ### Live Data Pipeline
    ```
    App startup
        ↓
    API wakes up (free tier cold start — once per 15 min idle)
        ↓
    Rosters fetched from ESPNcricinfo → stored in Supabase
        ↓
    Player dropdowns populated per team in real-time

    Every week (GitHub Actions)
        ↓
    Download latest IPL matches from Cricsheet.org
        ↓
    Retrain XGBoost model → push to Hugging Face → API reloads it
    ```

    ### Features Used
    | Input | How It's Used |
    |---|---|
    | **Playing 12** | Batting/bowling team composition |
    | **Venue** | Historical avg score at each ground |
    | **Pitch Report** | Adjusts score based on surface |
    | **Dew Factor** | Evening dew benefits batters |
    | **Toss** | Winner + decision adds contextual edge |
    | **Season** | Captures rule changes across IPL seasons |
    """)