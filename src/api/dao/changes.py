from typing import List
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from sqlalchemy import and_
from src.data.database import async_session_factory
from src.data.models import Match, Bet, BetChange, League, MatchMember
from src.data.schemas import BetDTO


class ChangesOrm:
    @staticmethod
    async def get_initial_points(match_id: int) -> List[BetDTO]:
        async with async_session_factory() as session:
            bet = aliased(Bet)
            initial_change_query = select(bet).select_from(bet) \
                .filter(bet.match_id == match_id, bet.version == 1)
            initial_change = await session.execute(initial_change_query)
            initial_change_orm = initial_change.scalars().all()
            initial_change_dto = [BetDTO.model_validate(row, from_attributes=True) for row in initial_change_orm]
            return initial_change_dto

    @staticmethod
    async def get_point_change(match_id: int):
        async with async_session_factory() as session:
            bc = aliased(BetChange)
            old_b = aliased(Bet)
            new_b = aliased(Bet)
            m = aliased(Match)
            mm_home = aliased(MatchMember)
            mm_away = aliased(MatchMember)
            le = aliased(League)

            change_query = select(old_b.home_cf,
                                  new_b.home_cf,
                                  old_b.away_cf,
                                  new_b.away_cf,
                                  old_b.point,
                                  new_b.point,
                                  old_b.type,
                                  old_b.period,
                                  new_b.created_at) \
                .select_from(bc) \
                .join(old_b, old_b.id == bc.old_bet_id) \
                .join(new_b, new_b.id == bc.new_bet_id) \
                .filter(old_b.match_id == match_id,
                        new_b.match_id == match_id) \
                .order_by(new_b.created_at.desc())

            match_query = select(m.id,
                                 mm_home.id,
                                 mm_home.name,
                                 mm_away.id,
                                 mm_away.name,
                                 m.start_time,
                                 le.name,
                                 le.id,
                                 ). \
                select_from(m). \
                join(le, le.id == m.league_id, isouter=True). \
                join(mm_home, and_(mm_home.match_id == m.id, mm_home.side == 'home'), isouter=True). \
                join(mm_away, and_(mm_away.match_id == m.id, mm_away.side == 'away'), isouter=True). \
                filter(m.id == match_id)

            changes = await session.execute(change_query)
            match = await session.execute(match_query)
            match = match.fetchone()
            initial_points = await ChangesOrm.get_initial_points(match_id)

            start_time = match[5]
            changes = [{'old_home_cf': change[0],
                        'new_home_cf': change[1],
                        'old_away_cf': change[2],
                        'new_away_cf': change[3],
                        'old_point': change[4],
                        'new_point': change[5],
                        'type': change[6],
                        'period': change[7],
                        'created_at': change[8]} for change in changes.fetchall()]
            league_link = match[6].replace(' ', '', 2).replace(' ', '-').replace('.', '')
            league_link = league_link.lower()
            home_name_link = match[2].replace(' ', '-').replace('/', '-').lower()
            away_name_link = match[4].replace(' ', '-').replace('/', '-').lower()
            link = (f'https://www.pinnacle.com/en/basketball/{league_link}/{home_name_link}'
                    f'-vs-{away_name_link}/{match[0]}/#all')

            data = {
                'initial_points': [{
                    'home_cf': ipoint.home_cf,
                    'away_cf': ipoint.away_cf,
                    'point': ipoint.point,
                    'type': ipoint.type,
                    'period': ipoint.period,
                    'created_at': ipoint.created_at
                } for ipoint in initial_points],
                'match': {
                    'link': link,
                    'match_id': match[0],
                    'home_id': match[1],
                    'home_name': match[2],
                    'away_id': match[3],
                    'away_name': match[4],
                    'start_time': start_time,
                    'league_name': match[6],
                    'league_id': match[7],
                },
                'changes': changes}

            return data
