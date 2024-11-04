import datetime
from typing import Optional

from src.data.models import BetTypeEnum, MatchSideEnum, MatchResultEnum
from pydantic import BaseModel
import uuid
from fastapi_users import schemas


class SportDTO(BaseModel):
    id: int
    name: str


class SportRelDTO(SportDTO):
    leagues: list['LeagueDTO']


class LeagueDTO(BaseModel):
    id: int
    sport_id: int
    name: str


class MatchDTO(BaseModel):
    id: int
    league_id: int
    start_time: datetime.datetime


class MatchUpcomingDTO(BaseModel):
    id: int
    start_time: datetime.datetime


class MatchMemberAddDTO(BaseModel):
    match_id: int
    name: str
    side: MatchSideEnum
    status: Optional[MatchResultEnum] = None


class MatchMemberDTO(MatchMemberAddDTO):
    id: int


class BetAddDTO(BaseModel):
    match_id: int
    point: float
    home_cf: float
    away_cf: float
    type: BetTypeEnum
    period: int
    created_at: datetime.datetime
    version: Optional[int] = None


class BetDTO(BetAddDTO):
    id: int


class BetChangeAddDTO(BaseModel):
    old_bet_id: int
    new_bet_id: int


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass
