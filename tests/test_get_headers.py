import asyncio

from sqlalchemy import select

from src.data.crud import SportOrm, LeagueOrm, MatchOrm, MatchMemberOrm, create_tables
from src.data.database import async_session_factory
from src.data.models import Match
from src.parser.collector.heads import collect_heads_data


def get_fake_heads():
    fakes_count = 3
    fakes = {'hasLive': [True, True, False, False],
             'id': [11, 12, 13, 14],
             'league_name': ['leagueName1', 'leagueName2', 'leagueName3', 'leagueName4'],
             'league_id': [21, 22, 23, 24],
             'homeName': ['homeName1', 'homeName2', 'homeName3', 'homeName4'],
             'awayName': ['awayName1', 'awayName2', 'awayName3', 'awayName4'],
             'startTime': ['2030-09-10T23:00:00Z', '2000-09-10T23:00:00Z', '2000-09-10T23:00:00Z', '2030-09-10T23:00:00Z'],
             'type': ['matchup', 'notmathup', 'matchup', 'matchup']}

    heads = []
    for idx in range(fakes_count):
        heads.append({'hasLive': fakes['hasLive'][idx],
                      'id': fakes['id'][idx],
                      'isLive': False,
                      'league': {
                          'id': fakes['league_id'][idx],
                          'name': fakes['league_name'][idx],
                          'sport': {'id': 4, 'name': 'Basketball'}
                      },
                      'participants':
                          [{'alignment': 'home', 'name': fakes['homeName'][idx]},
                           {'alignment': 'away', 'name': fakes['awayName'][idx]}],
                      'startTime': fakes['startTime'][idx],
                      'type': fakes['type'][idx]})
    return heads


async def test_count_of_heads():
    heads = get_fake_heads()
    await create_tables()
    await collect_heads_data(heads)
    async with async_session_factory() as session:
        query = select(Match)
        result = await session.execute(query)
        result = result.all()
        assert len(result) == 0, 'Length of matches'

if __name__ == "__main__":
    asyncio.run(test_count_of_heads())
