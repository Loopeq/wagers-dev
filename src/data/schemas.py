import datetime
from datetime import timedelta
from typing import Optional

from src.data.models import BetTypeEnum, MatchSideEnum, MatchResultEnum, BetStatusEnum, BetValueTypeEnum
from pydantic import BaseModel, field_validator


class SportDTO(BaseModel):
    id: int
    name: str


class SportRelDTO(SportDTO):
    leagues: list['LeagueDTO']


class LeagueDTO(BaseModel):
    id: int
    sport_id: int
    name: str


class LeagueRelDTO(LeagueDTO):
    sport: 'SportDTO'
    matches: list['MatchDTO']


class MatchDTO(BaseModel):
    id: int
    league_id: int
    start_time: datetime.datetime


class MatchRelDTO(MatchDTO):
    league: 'LeagueDTO'
    match_members: list['MatchMemberDTO']
    bets: list['BetDTO']


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


class MatchMemberRelDTO(MatchMemberDTO):
    match: 'MatchDTO'


class BetAddDTO(BaseModel):
    match_id: int
    type: BetTypeEnum
    period: int


class BetDTO(BetAddDTO):
    id: int


class BetRelDTO(BetDTO):
    bet_values: list['BetValueDTO']
    match: MatchDTO


class BetValueAddDTO(BaseModel):
    bet_id: int
    value: float
    version: Optional[int] = None
    point: Optional[float] = None
    status: BetStatusEnum
    type: BetValueTypeEnum
    created_at: datetime.datetime


class BetValueDTO(BetValueAddDTO):
    id: int


class BetValueRelDTO(BetValueDTO):
    bet: 'BetDTO'


