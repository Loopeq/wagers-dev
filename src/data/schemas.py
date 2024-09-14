import datetime
from datetime import timedelta
from typing import Optional

from src.data.models import BetTypeEnum, MatchSideEnum, MatchResultEnum
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


class MatchMemberAddDTO(BaseModel):
    match_id: int
    name: str
    status: Optional[MatchResultEnum]
    side: MatchSideEnum


class MatchMemberDTO(MatchMemberAddDTO):
    id: int


class MatchMemberRelDTO(MatchMemberDTO):
    match: 'MatchDTO'
    bets: list['BetDTO']


class BetAddDTO(BaseModel):
    match_member_id: int
    type: BetTypeEnum
    period: int
    created_at: datetime.datetime


class BetDTO(BetAddDTO):
    id: int


class BetRelDTO(BetDTO):
    match_member: 'MatchMemberDTO'
    bet_values: list['BetValueDTO']


class BetValueAddDTO(BaseModel):
    bet_id: int
    value: float
    point: Optional[float]


class BetValueDTO(BaseModel):
    id: int


class BetValueRelDTO(BetValueDTO):
    bet: 'BetDTO'


def valid():
    match = MatchDTO(id=1, league_id=2, start_time=datetime.datetime.utcnow() + timedelta(minutes=30))


if __name__ == '__main__':
    valid()
