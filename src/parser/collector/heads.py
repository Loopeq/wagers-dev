import asyncio
import datetime

from src.parser.calls.base import Status
from src.parser.calls.matchups import get_match_up_response
from src.data.models import MatchSideEnum
from src.parser.utils.common import iso_to_utc
from src.data.crud import MatchOrm, UpdateManager
from src.data.schemas import SportDTO, LeagueDTO, MatchDTO, MatchMemberAddDTO
from src.logs import logger


async def collect_heads_data(data: list[dict]):
    count = 0
    logger.info(f'Start collecting for {len(data)} head matches')
    tasks = []
    for event in data:
        event_type = event.get('type')
        start_time = iso_to_utc(event.get('startTime'))
        now_date = datetime.datetime.utcnow()
        isLive = event.get('isLive')
        match_id = event.get('id')

        if (event_type != 'matchup') or now_date >= start_time or isLive:
            continue

        exists = await MatchOrm.exists_match_by_id(match_id)
        if exists:
            continue

        count += 1
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

        tasks.append(UpdateManager.insert_match(sport_dto, league_dto, match_dto, match_member_home_dto,
                                                match_member_away_dto))

    await asyncio.gather(*tasks)
    logger.info(f'Finish collecting for {count} head matches')


async def collect_heads():
    match_ups_response = await get_match_up_response(4)
    if match_ups_response.status == Status.DENIED:
        return
    await collect_heads_data(data=match_ups_response.data)


