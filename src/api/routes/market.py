from datetime import datetime, timedelta
import json
import math
from typing import Annotated
from curl_cffi import AsyncSession
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func, select
from src.core.db.db_helper import db_helper
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.models import League, Match, Sport
from src.core.schemas import SportDTO
import asyncio

from src.services.related_service import RelatedService
from src.services.straight_service import StraightService

router = APIRouter(prefix="/market", tags=["Market"])


async def event_generator():
    counter = 0
    while counter < 10:
        data = {"message": f"ping {counter}"}
        yield f"data: {json.dumps(data)}\n\n"
        counter += 1
        await asyncio.sleep(1)


@router.get("/ping")
async def ping():
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/sports", response_model=list[SportDTO])
async def load_sports(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    stmt = (
        select(Sport.id, Sport.name, func.count(Match.id).label("match_count"))
        .outerjoin(League, League.sport_id == Sport.id)
        .outerjoin(Match, Match.league_id == League.id)
        .where(Match.start_time > datetime.utcnow())
        .group_by(Sport.id, Sport.name)
        .order_by(desc(func.count(Match.id)))
    )

    result = await session.execute(stmt)
    return [
        {"id": s.id, "name": s.name.title(), "match_count": s.match_count}
        for s in result.all()
    ]


@router.get("/related")
async def load_related(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    sport_id: int,
    league_id: int | None = None,
    hours: int | None = None,
    finished: bool = False,
    nulls: bool = False,
    sort_by: str = "team_name",
    sort_order: str = "ASC",
    offset: int = 0,
    limit: int = 20,
):
    return await RelatedService.get_related(
        session=session,
        sport_id=sport_id,
        league_id=league_id,
        hours=hours,
        finished=finished,
        nulls=nulls,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
    )


@router.get("/straight")
async def load_straight(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    match_id: int,
    child_id: int | None = None,
):
    return await StraightService.load_straight(match_id, child_id, session)


@router.get("/history")
async def get_history(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    home_id: int,
    away_id: int,
    current_match_id: int,
):
    return await RelatedService.get_history(
        home_id=home_id,
        away_id=away_id,
        current_match_id=current_match_id,
        session=session,
    )
