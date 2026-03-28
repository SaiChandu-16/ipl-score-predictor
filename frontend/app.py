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

# ── Data fetchers (cached) ────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)   # Cache teams for 1 hour
def fetch_teams() -> dict:
    """Returns {team_name: {short_name, home_ground, ...}}"""
    try:
        resp = requests.get(f"{API_URL}/teams/", timeout=15)
        resp.raise_for_status()
        data = resp.json()
        teams = {t["name"]: t for t in data["teams"]}
        return teams, data.get("rosters_last_updated")
    except Exception as e:
        st.warning(f"Could not fetch live teams: {e}. Using defaults.")
        return _default_teams(), None


@st.cache_data(ttl=3600, show_spinner=False)   # Cache each team's players for 1 hour
def fetch_players(team_name: str) -> list[dict]:
    """Returns list of player dicts for a team."""
    try:
        resp = requests.get(
            f"{API_URL}/teams/{requests.utils.quote(team_name)}/players",
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("players", [])
    except Exception as e:
        return []


def _default_teams() -> dict:
    """Fallback team list when API is unreachable."""
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
    "Batter": "🏏",
    "WK-Batter": "🧤",
    "All-rounder": "⚡",
    "Bowler": "🎳",
    "Unknown": "❓",
}

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏏 IPL Score Predictor")
st.caption("Predict innings scores using live IPL rosters, pitch conditions, and toss result.")
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Predict", "📋 History & Accuracy", "👥 Team Squads", "📖 How it Works"
])

# ═══════════════════════════════════════════════
# TAB 1 — PREDICT
# ═══════════════════════════════════════════════
with tab1:
    # Load teams
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

        # Auto-suggest home ground as venue
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
        pitch_hardness = st.slider(
            "Pitch Hardness", 1, 10, 7,
            help="1 = very soft/crumbly (spinner's paradise), 10 = very hard (pace-friendly)"
        )
        dew_factor = st.toggle("🌫️ Dew Expected?", value=False)
        if dew_factor:
            st.info("Dew typically helps the chasing team — batters get an advantage in the 2nd innings.")

    st.divider()
    st.subheader("🎲 Toss")
    col3, col4 = st.columns(2)
    with col3:
        toss_winner = st.selectbox("Toss Winner", [batting_team, bowling_team])
    with col4:
        toss_decision = st.radio("Elected to", ["Bat", "Field"], horizontal=True)

    # ── Player Selection ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("👥 Select Playing 12")
    st.caption("Players are loaded from live IPL rosters. Select the playing XI/XII for each team.")

    # Fetch players for both teams in parallel-ish
    with st.spinner(f"Loading {batting_team} squad..."):
        batting_players_all = fetch_players(batting_team)
    with st.spinner(f"Loading {bowling_team} squad..."):
        bowling_players_all = fetch_players(bowling_team)

    def player_label(p: dict) -> str:
        emoji = ROLE_EMOJI.get(p.get("role", "Unknown"), "❓")
        country = p.get("country", "")
        flag = " 🌍" if country not in ("India", "") else ""
        return f"{emoji} {p['name']}{flag}"

    def player_names(players: list) -> list[str]:
        return [p["name"] for p in players]

    col5, col6 = st.columns(2)

    with col5:
        st.markdown(f"**{batting_team}**")

        if batting_players_all:
            # Group by role for display
            bat_by_role = {}
            for p in batting_players_all:
                bat_by_role.setdefault(p.get("role", "Unknown"), []).append(p["name"])

            # Show role breakdown as info
            role_summary = " · ".join(
                f"{ROLE_EMOJI.get(r, '❓')} {r}: {len(ps)}"
                for r, ps in bat_by_role.items()
            )
            st.caption(role_summary)

            batting_selected = st.multiselect(
                f"Select {batting_team} players",
                options=player_names(batting_players_all),
                default=player_names(batting_players_all)[:6],
                max_selections=7,
                key="bat_players",
                help="Select 5–7 players from the batting team",
            )
        else:
            st.warning(f"Could not load {batting_team} squad. Check API connection.")
            batting_selected = st.multiselect(
                f"Enter {batting_team} players manually",
                options=[],
                key="bat_players",
            )

    with col6:
        st.markdown(f"**{bowling_team}**")

        if bowling_players_all:
            bowl_by_role = {}
            for p in bowling_players_all:
                bowl_by_role.setdefault(p.get("role", "Unknown"), []).append(p["name"])

            role_summary = " · ".join(
                f"{ROLE_EMOJI.get(r, '❓')} {r}: {len(ps)}"
                for r, ps in bowl_by_role.items()
            )
            st.caption(role_summary)

            # Exclude already-selected batting players
            available_bowl = [
                p["name"] for p in bowling_players_all
                if p["name"] not in batting_selected
            ]

            bowling_selected = st.multiselect(
                f"Select {bowling_team} players",
                options=available_bowl,
                default=available_bowl[:5],
                max_selections=6,
                key="bowl_players",
                help="Select 4–6 players from the bowling team",
            )
        else:
            st.warning(f"Could not load {bowling_team} squad. Check API connection.")
            bowling_selected = st.multiselect(
                f"Enter {bowling_team} players manually",
                options=[],
                key="bowl_players",
            )

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
                "batting_team": batting_team,
                "bowling_team": bowling_team,
                "venue": venue,
                "playing_12": playing_12,
                "batting_team_players": batting_selected,
                "bowling_team_players": bowling_selected,
                "pitch_type": pitch_type,
                "pitch_hardness": pitch_hardness,
                "dew_factor": dew_factor,
                "toss_winner": toss_winner,
                "toss_decision": toss_decision,
                "match_time": match_time,
                "season": season,
            }

            with st.spinner("Computing prediction..."):
                try:
                    res = requests.post(f"{API_URL}/predict/", json=payload, timeout=30)
                    res.raise_for_status()
                    data = res.json()

                    st.session_state["last_prediction_id"]    = data["prediction_id"]
                    st.session_state["last_predicted_score"]  = data["predicted_score"]

                    st.success("✅ Prediction ready!")

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("🏏 Predicted Score", f"{data['predicted_score']} runs")
                    m2.metric("📉 Low Estimate",  f"{data['confidence_range']['low']} runs")
                    m3.metric("📈 High Estimate", f"{data['confidence_range']['high']} runs")
                    m4.metric("🤖 Model",         data["model_version"])

                    st.subheader("📊 Phase-wise Breakdown")
                    phases = data["phase_breakdown"]
                    phase_df = pd.DataFrame({
                        "Phase": ["Powerplay (1–6)", "Middle Overs (7–15)", "Death Overs (16–20)"],
                        "Predicted Runs": [
                            phases["powerplay"],
                            phases["middle_overs"],
                            phases["death_overs"],
                        ],
                    })
                    st.bar_chart(phase_df.set_index("Phase"))

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot reach the API. The server may be waking up — try again in 30s.")
                except Exception as e:
                    st.error(f"Prediction error: {e}")

    # ── Feedback ───────────────────────────────────────────────────────────────
    if "last_prediction_id" in st.session_state:
        st.divider()
        st.subheader("✅ Submit Actual Score (after the match)")
        st.caption("Your feedback directly improves future predictions via weekly retraining.")

        with st.form("feedback_form"):
            actual_score = st.number_input("Actual Score Scored", min_value=0, max_value=350, step=1)
            user_rating  = st.slider("Rate this prediction (1 = very off, 5 = spot on)", 1, 5, 3)
            comments     = st.text_input("Comments (optional)")
            submit_fb    = st.form_submit_button("📤 Submit Feedback")

        if submit_fb:
            fb_payload = {
                "prediction_id": st.session_state["last_prediction_id"],
                "actual_score":  actual_score,
                "user_rating":   user_rating,
                "comments":      comments,
            }
            try:
                fb_res = requests.post(f"{API_URL}/feedback/", json=fb_payload, timeout=15)
                fb_res.raise_for_status()
                pred  = st.session_state["last_predicted_score"]
                error = abs(pred - actual_score)
                pct   = round(error / max(actual_score, 1) * 100, 1)
                st.success(
                    f"Thank you! Prediction was off by **{error} runs** ({pct}%). "
                    "This helps retrain the model 🏏"
                )
            except Exception as e:
                st.error(f"Feedback error: {e}")

    # ── Roster refresh button ──────────────────────────────────────────────────
    with st.expander("🔄 Force roster refresh from ESPNcricinfo"):
        st.caption("Use this if you think squads have changed (e.g. after IPL auction).")
        if st.button("Refresh Rosters Now"):
            try:
                r = requests.post(f"{API_URL}/teams/refresh", timeout=10)
                r.raise_for_status()
                st.success("Roster refresh triggered! Clear cache and reload in ~30 seconds.")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Could not trigger refresh: {e}")

# ═══════════════════════════════════════════════
# TAB 2 — HISTORY
# ═══════════════════════════════════════════════
with tab2:
    st.subheader("📋 Past Predictions & Accuracy")
    col_r, col_l = st.columns([1, 5])
    with col_r:
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
                "Date":         r["created_at"][:10],
                "Batting Team": r["inputs"].get("batting_team", "—"),
                "Venue":        r["inputs"].get("venue", "—"),
                "Predicted":    r["predicted_score"],
                "Actual":       r.get("actual_score") or "—",
                "Error (runs)": abs(r["predicted_score"] - r["actual_score"])
                                if r.get("actual_score") else "—",
                "⭐ Rating":    r.get("user_rating") or "—",
                "Model":        r.get("model_version", "—"),
            } for r in records])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Error distribution chart for labeled records
            labeled = [r for r in records if r.get("actual_score")]
            if labeled:
                st.subheader("📈 Prediction Error Distribution")
                errors = [abs(r["predicted_score"] - r["actual_score"]) for r in labeled]
                err_df = pd.DataFrame({"Absolute Error (runs)": errors})
                st.bar_chart(err_df["Absolute Error (runs)"].value_counts().sort_index())
        else:
            st.info("No predictions yet. Make your first one in the Predict tab!")
    except Exception as e:
        st.warning(f"Could not load history: {e}")

# ═══════════════════════════════════════════════
# TAB 3 — TEAM SQUADS
# ═══════════════════════════════════════════════
with tab3:
    st.subheader("👥 Current IPL Squads")
    st.caption("All rosters are fetched live from ESPNcricinfo and refreshed every 24 hours.")

    teams_data_sq, last_updated_sq = fetch_teams()
    if last_updated_sq:
        try:
            dt = datetime.fromisoformat(last_updated_sq)
            st.info(f"📡 Last refreshed: {dt.strftime('%d %b %Y at %H:%M UTC')}")
        except Exception:
            pass

    selected_team = st.selectbox("Choose a team to view squad", sorted(teams_data_sq.keys()))

    if selected_team:
        with st.spinner(f"Loading {selected_team} squad..."):
            squad = fetch_players(selected_team)

        if squad:
            # Group by role
            by_role = {}
            for p in squad:
                by_role.setdefault(p.get("role", "Unknown"), []).append(p)

            role_order = ["Batter", "WK-Batter", "All-rounder", "Bowler", "Unknown"]
            cols = st.columns(2)
            col_idx = 0

            for role in role_order:
                if role not in by_role:
                    continue
                with cols[col_idx % 2]:
                    emoji = ROLE_EMOJI.get(role, "❓")
                    st.markdown(f"**{emoji} {role}s**")
                    for p in by_role[role]:
                        flag = "🌍" if p.get("country", "India") != "India" else "🇮🇳"
                        st.markdown(
                            f"&nbsp;&nbsp;{flag} {p['name']} "
                            f"<small style='color:gray'>({p.get('country', '?')})</small>",
                            unsafe_allow_html=True,
                        )
                    st.markdown("")
                col_idx += 1
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
    Fetch current IPL rosters from ESPNcricinfo (every 24h)
        ↓
    Store in Supabase → power the player dropdowns in real-time

    Every week (GitHub Actions)
        ↓
    Download latest IPL match data from Cricsheet.org
        ↓
    Append new labeled matches to Supabase
        ↓
    Retrain XGBoost model on updated data
        ↓
    Push improved model to Hugging Face → API auto-loads it
    ```

    ### Prediction Features

    | Input | How It's Used |
    |---|---|
    | **Playing 12** | Identifies batting/bowling strength of each team |
    | **Venue** | Historical avg score at each ground |
    | **Pitch Report** | Modifies predicted score based on surface type |
    | **Pitch Hardness** | Hard = faster, more batting-friendly |
    | **Dew Factor** | Evening dew gives batting team a bonus |
    | **Toss** | Toss winner + decision adds a contextual edge |
    | **Season** | Captures rule and format changes over IPL seasons |

    ### Continuous Learning
    Every time you submit an actual score after a match:
    - It gets stored in Supabase as a new labeled training example
    - The weekly GitHub Actions job retrains the model
    - A new model only goes live if its error is **lower** than the current one
    - You can see the model's accuracy improving in the History tab
    """)
