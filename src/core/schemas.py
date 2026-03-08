import datetime
from typing import Optional
from pydantic import BaseModel

from src.core.models import MatchSideEnum


class SportDTO(BaseModel):
    id: int
    name: str
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
    parent_id: int | None = None
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
    draw_cf: float | None = None
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


class UserOut(BaseModel):
    email: str
    disabled: bool
    superuser: bool


class UserOutAdmin(UserOut):
    created_at: datetime.datetime


class InviteCode(BaseModel):
    user_email: str | None
    code: str
    created_at: datetime.datetime
    is_used: bool


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


class MatchResultDTO(BaseModel):
    match_id: int
    period: int
    description: str
    team_1_score: int
    team_2_score: int


class RegisterForm(BaseModel):
    email: str
    password: str
    invite_code: str
