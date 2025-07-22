import datetime
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from src.core.models import MatchSideEnum


class SportDTO(BaseModel):
    id: int
    name: str
    name_ru: str
    match_count: int


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
    sport_id: int
    start_time: datetime.datetime


class MatchMemberAddDTO(BaseModel):
    match_id: int
    name: str
    side: MatchSideEnum


class MatchMemberDTO(MatchMemberAddDTO):
    id: int


class BetAddDTO(BaseModel):
    match_id: int
    point: float | None = None
    home_cf: float
    away_cf: float
    max_limit: int
    type: str
    period: int
    key: str
    created_at: datetime.datetime
    version: Optional[int] = None


class BetDTO(BetAddDTO):
    id: int


class BetChangeAddDTO(BaseModel):
    old_bet_id: int
    new_bet_id: int


class BaseUser(BaseModel):
    disabled: bool
    location: str
    superuser: bool


class UserOut(BaseUser):
    uuid: UUID


class UserInDB(BaseUser):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    uuid: UUID | None = None


class MatchResultDTO(BaseModel):
    match_id: int
    period: int
    description: str
    team_1_score: int
    team_2_score: int
