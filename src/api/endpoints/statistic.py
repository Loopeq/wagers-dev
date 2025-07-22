from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.crud.api.straight import get_team_games, get_search_items, get_leagues as fetch_leagues, \
    get_teams as fetch_teams
from src.core.db.db_helper import db_helper

router = APIRouter(prefix="/statistic", tags=["Statistic"])


@router.get("")
async def get_statistic(current_user: CURRENT_ACTIVE_USER,
                        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
                        team_id: int):
    games = await get_team_games(team_id=team_id, session=session)
    return games


@router.get("/leagues")
async def get_leagues(current_user: CURRENT_ACTIVE_USER,
                      session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
                      sport_id: int):
    leagues = await fetch_leagues(sport_id=sport_id, session=session)
    return leagues


@router.get("/teams")
async def get_teams(current_user: CURRENT_ACTIVE_USER,
                    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
                    sport_id: int, league_id: int | None = None):
    teams = await fetch_teams(sport_id=sport_id, league_id=league_id, session=session)
    return teams


@router.get("/search")
async def get_search(current_user: CURRENT_ACTIVE_USER,
                     session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
                     query: str, sport_id: int):
    result = await get_search_items(query=query, sport_id=sport_id, session=session)
    return result


@router.get("/history")
async def get_history(current_user: CURRENT_ACTIVE_USER,
                      session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
                      home_id: int,
                      away_id: int,
                      current_match_id: int):
    home_history = await get_team_games(team_id=home_id, current_match_id=current_match_id, session=session)
    away_history = await get_team_games(team_id=away_id, current_match_id=current_match_id, session=session)

    return {
        'home': home_history,
        'away': away_history
    }
