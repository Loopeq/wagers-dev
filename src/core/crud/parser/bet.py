from datetime import timedelta, datetime
from typing import List

from sqlalchemy import func, select, Select

from src.core.schemas import BetAddDTO
from src.parser.config import accuracy_near, accuracy_far, accuracy_hour
from src.core.db.db_helper import db_helper
from src.core.models import Bet


async def get_last_point_stmt(match_id: int, type: str, period: int):
    """ Returns point and max version """
    stmt = select(func.max(Bet.version), Bet.point).select_from(Bet).filter(Bet.match_id == match_id,
                                                                            Bet.type == type,
                                                                            Bet.period == period).group_by(Bet.point)
    return stmt


async def insert_bets(bets: List[BetAddDTO], match_id: int):
    bet_created_at = datetime.utcnow()
    async with db_helper.session_factory() as session:
        bets_orm = []
        for bet in bets:
            last_point_stmt: Select = await get_last_point_stmt(match_id=match_id, type=bet.type, period=bet.period)
            version_an_point = last_point_stmt.add_columns(Bet.created_at).group_by(Bet.created_at)
            result = await session.execute(version_an_point)
            row = result.fetchone()

            if row:
                max_version, point, created_at = row
                time_condition = created_at + timedelta(hours=accuracy_hour) > datetime.utcnow()
                point_difference = abs(bet.point - point)

                if (time_condition and point_difference >= accuracy_near) or (
                        not time_condition and point_difference >= accuracy_far):
                    bets_orm.append(create_bet(match_id, bet, max_version + 1, bet_created_at))
            else:
                bets_orm.append(create_bet(match_id, bet, 1, bet_created_at))

        session.add_all(bets_orm)
        await session.commit()


def create_bet(match_id: int, bet: BetAddDTO, version: int, created_at: datetime) -> Bet:
    return Bet(
            match_id=match_id,
            point=bet.point,
            home_cf=bet.home_cf,
            away_cf=bet.away_cf,
            type=bet.type,
            period=bet.period,
            version=version,
            created_at=created_at
    )
