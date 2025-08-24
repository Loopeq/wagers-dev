from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from src.core.db.db_helper import db_helper
from src.core.models import Match, League, MatchMember, Team, MatchResult
from src.core.schemas import MatchUpcomingDTO, MatchResultDTO
import logging
from src.parser.config import clear_threshold, sports


async def check_exist(ids: list):
    async with db_helper.session_factory() as session:
        query = select(Match.id).filter(Match.id.in_(ids))
        result = await session.execute(query)
        return {row[0] for row in result.all()}


async def add_match_cascade(league: League, match: Match, team_home: Team,
                            team_away: Team):
    async with db_helper.session_factory() as session:
        async with session.begin():
            try:
                await session.execute(insert(League).values(
                    id=league.id,
                    sport_id=league.sport_id,
                    name=league.name).on_conflict_do_nothing())
                await session.execute(
                    insert(Match).values(
                        id=match.id,
                        parent_id=match.parent_id,
                        league_id=match.league_id,
                        start_time=match.start_time).on_conflict_do_nothing())
                home_id = await session.execute(
                    insert(Team).values(
                        name=team_home.name,
                        league_id=league.id
                    ).on_conflict_do_update(
                        index_elements=['name', 'league_id'],
                        set_={'name': team_home.name}
                    )
                    .returning(Team.id)
                )
                home_id = home_id.scalar()

                away_id = await session.execute(
                    insert(Team).values(
                        name=team_away.name,
                        league_id=league.id
                    ).on_conflict_do_update(
                        index_elements=['name', 'league_id'],
                        set_={'name': team_away.name}
                    )
                    .returning(Team.id)
                )
                away_id = away_id.scalar()
                if home_id and away_id:
                    await session.execute(
                        insert(MatchMember).values(
                            match_id=match.id,
                            home_id=home_id,
                            away_id=away_id,
                        ).on_conflict_do_nothing()
                    )
            except:
                logging.error(f'Error while add header for Match: {match.to_dict()}. League: {league.to_dict()}')
                raise


async def get_upcoming_matches(sport_id: int = None):
    async with db_helper.session_factory() as session:
        current_time = datetime.utcnow()
        query = select(Match.start_time, Match.id, Match.parent_id, League.sport_id).outerjoin(League, League.id == Match.league_id)
        if sport_id: 
            query.filter(League.sport_id == sport_id)
        query = query.filter(Match.start_time > current_time)
        result = await session.execute(query)
        matches = result.fetchall()
        matches_dto = [MatchUpcomingDTO.model_validate(row, from_attributes=True) for row in matches]
        return matches_dto


async def add_match_results(match_results: List[MatchResultDTO]):
    async with db_helper.session_factory() as session:
        ids = [match_result.match_id for match_result in match_results]
        existing_ids_result = await session.execute(
            select(Match.id)
            .filter(
                Match.id.in_(ids),
                ~Match.id.in_(select(MatchResult.match_id))
            )
        )
        existing_ids = existing_ids_result.scalars().all()
        valid_results = [match for match in match_results if match.match_id in existing_ids]
        if not valid_results:
            return
        stmt = insert(MatchResult).values([
            {
                'match_id': int(r.match_id),
                'period': r.period,
                'description': r.description,
                'team_1_score': r.team_1_score,
                'team_2_score': r.team_2_score,
            }
            for r in valid_results
        ]).on_conflict_do_nothing(
            index_elements=['match_id', 'period']
        )

        await session.execute(stmt)
        await session.commit()


async def clear_events_by_start_time():
    async with db_helper.session_factory() as session:
        current_time = datetime.utcnow()
        subquery = (
            select(Match.id)
            .join(League, Match.league_id == League.id)
            .where(
                Match.start_time < current_time - timedelta(days=int(clear_threshold)),
                League.sport_id != sports['tennis']
            )
        )

        stmt = delete(Match).where(Match.id.in_(subquery))
        await session.execute(stmt)

        await session.commit()
