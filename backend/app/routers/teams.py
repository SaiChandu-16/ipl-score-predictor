"""
app/routers/teams.py
---------------------
Endpoints to fetch IPL teams and their current squad rosters.
The frontend calls these at load time to populate dropdowns dynamically.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from app.services.cricket_data_service import (
    get_all_teams,
    get_players_for_team,
    refresh_all_rosters,
    get_rosters_last_updated,
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def list_teams():
    """
    Return all 10 IPL teams with metadata.
    Used to populate the batting/bowling team dropdowns.
    """
    try:
        teams = get_all_teams()
        last_updated = get_rosters_last_updated()
        return {
            "teams": teams,
            "rosters_last_updated": last_updated,
            "count": len(teams),
        }
    except Exception as e:
        logger.error(f"Failed to fetch teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{team_name}/players")
async def team_players(
    team_name: str,
    role: str = Query(default=None, description="Filter by role: Batter, Bowler, All-rounder, WK-Batter"),
):
    """
    Return the current active squad for a specific team.
    Optionally filter by player role.

    Example:
        GET /teams/Chennai Super Kings/players
        GET /teams/Mumbai Indians/players?role=Bowler
    """
    try:
        players = get_players_for_team(team_name)

        if not players:
            raise HTTPException(
                status_code=404,
                detail=f"No players found for '{team_name}'. Try refreshing rosters."
            )

        if role:
            players = [p for p in players if role.lower() in p.get("role", "").lower()]

        # Group by role for better frontend display
        grouped = {}
        for p in players:
            r = p.get("role", "Unknown")
            grouped.setdefault(r, []).append(p)

        return {
            "team": team_name,
            "total_players": len(players),
            "players": players,
            "by_role": grouped,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch players for {team_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def trigger_roster_refresh(background_tasks: BackgroundTasks):
    """
    Trigger a background roster refresh from ESPNcricinfo.
    Called automatically on app startup and by the GitHub Actions weekly job.
    Returns immediately; refresh happens in background.
    """
    background_tasks.add_task(_run_refresh)
    return {
        "status": "refresh_started",
        "message": "Roster refresh triggered in background. Check /teams for updated data in ~30s.",
    }


async def _run_refresh():
    try:
        summary = refresh_all_rosters(use_scraping=True)
        logger.info(f"Background roster refresh complete: {summary}")
    except Exception as e:
        logger.error(f"Background roster refresh failed: {e}")
        # Fall back to hardcoded squads
        refresh_all_rosters(use_scraping=False)
