import asyncio
import datetime
import json
from datetime import timedelta
from pathlib import Path

from src.calls.matchups import get_match_up_response
from src.data.models import MatchSideEnum, BetTypeEnum
from src.utils.common import iso_to_utc
from src.data.crud import SportOrm, LeagueOrm, MatchOrm, MatchMemberOrm, BetOrm, create_tables
from src.data.schemas import SportDTO, LeagueDTO, MatchDTO, MatchMemberAddDTO, BetAddDTO


async def collect_heads():
    match_ups_response = await get_match_up_response(4)
    await _collect_heads_data(data=match_ups_response.data)


async def _collect_heads_data(data: list[dict]):
    for event in data:
        has_live = event.get('hasLive')
        event_type = event.get('type')
        start_time = iso_to_utc(event.get('startTime'))
        utc_now_time = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0, tzinfo=None)
        delta = timedelta(days=1)
        # TODO: DEV
        if has_live or (start_time < utc_now_time + delta) or event_type != 'matchup':
            continue

        match_id = event.get('id')
        league = event.get('league')
        league_id = league.get('id')
        league_name = league.get('name')
        sport = league.get('sport')
        sport_name = sport.get('name')
        sport_id = sport.get('id')
        participants = event.get('participants')
        home_team, away_team = participants[0], participants[1]
        home_name, away_name = home_team.get('name'), away_team.get('name')

        sport_dto = SportDTO(id=sport_id, name=sport_name)
        league_dto = LeagueDTO(id=league_id, sport_id=sport_id, name=league_name)
        match_dto = MatchDTO(id=match_id, league_id=league_id, start_time=start_time)
        match_member_home_dto = MatchMemberAddDTO(match_id=match_id, name=home_name, side=MatchSideEnum.home)
        match_member_away_dto = MatchMemberAddDTO(match_id=match_id, name=away_name, side=MatchSideEnum.away)

        await SportOrm.insert_sport(sport_dto)
        await LeagueOrm.insert_league(league_dto)
        await MatchOrm.insert_match(match_dto)
        await MatchMemberOrm.insert_match_member(match_member_home_dto)
        await MatchMemberOrm.insert_match_member(match_member_away_dto)

        periods = event.get('periods')
        await collect_periods(periods, match_id=match_id)


async def collect_periods(periods: list[dict], match_id: int) -> None:
    has_types = ['hasMoneyline', 'hasSpread', 'hasTeamTotal', 'hasTotal']
    types = {'hasMoneyline': 'moneyline', 'hasSpread': 'spread', 'hasTeamTotal': 'teamtotal', 'hasTotal': 'total'}
    bets_to_add = []
    for period in periods:
        period_count = period.get('period')
        for w_type in has_types:
            if period.get(w_type):
                bet = BetAddDTO(match_id=match_id, type=BetTypeEnum[types[w_type]], period=period_count)
                bets_to_add.append(bet)
    await BetOrm.insert_bets(bets_to_add)

