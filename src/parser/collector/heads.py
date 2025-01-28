import asyncio
import datetime
from src.parser.base import Status
from src.parser.calls.matchups import get_match_up_response
from src.core.models import MatchSideEnum, League, Match, MatchMember
from src.parser.collector.content import collect_content
from src.parser.config import parse_content, parse_allow_types
from src.parser.utils.common import iso_to_utc
from src.core.crud.parser.match import check_exist, add_match_cascade


async def collect_heads_data(data: list[dict], name: str):
    count = 0
    tasks = []
    for event in data:
        event_type = event.get('type')
        start_time = iso_to_utc(event.get('startTime'))
        now_date = datetime.datetime.utcnow()
        isLive = event.get('isLive')
        match_id = event.get('id')

        if (event_type != 'matchup') or (now_date >= start_time) or isLive:
            continue

        exist = await check_exist(id=match_id)
        if exist:
            continue

        count += 1
        league = event.get('league')
        league_id = league.get('id')
        league_name = league.get('name')
        sport = league.get('sport')
        sport_id = sport.get('id')
        participants = event.get('participants')
        home_team, away_team = participants[0], participants[1]
        home_name, away_name = home_team.get('name'), away_team.get('name')

        league_orm = League(id=league_id, sport_id=sport_id, name=league_name)
        match_orm = Match(id=match_id, league_id=league_id, start_time=start_time)
        match_member_home_orm = MatchMember(match_id=match_id, name=home_name, side=MatchSideEnum.home)
        match_member_away_orm = MatchMember(match_id=match_id, name=away_name, side=MatchSideEnum.away)

        tasks.append(add_match_cascade(league=league_orm,
                                       match=match_orm,
                                       match_member_home=match_member_home_orm,
                                       match_member_away=match_member_away_orm))
    if tasks:
        await asyncio.gather(*tasks)
    else:
        pass


async def collect_heads(sports: dict):
    for name in sports.keys():
        match_ups_response = await get_match_up_response(event_id=sports[name])
        if match_ups_response.status == Status.DENIED:
            return
        await collect_heads_data(data=match_ups_response.data, name=name)
    await collect_content(start=parse_content[2]['start'], end=parse_content[2].get('end'),
                          parse_allow_types=parse_allow_types)


