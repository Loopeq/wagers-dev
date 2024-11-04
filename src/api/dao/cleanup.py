from sqlalchemy import select, func, and_, delete, not_

from src.data.database import async_session_factory
from src.data.models import BetChange, Bet
from src.logs import logger


class CleanUpOrm:

    @staticmethod
    async def remove_unref_changes():
        bet_change_subquery = (
            select(BetChange.old_bet_id)
            .union(select(BetChange.new_bet_id))
        ).subquery()

        max_version_subquery = (
            select(
                Bet.match_id,
                Bet.period,
                Bet.type,
                func.max(Bet.version).label('max_version')
            )
            .group_by(Bet.match_id, Bet.period, Bet.type)
        ).subquery()

        delete_query = (
            delete(Bet)
            .where(
                and_(
                    Bet.id.notin_(select(bet_change_subquery)),
                    Bet.version != 1,
                    not_(
                        and_(
                            Bet.match_id.in_(select(max_version_subquery.c.match_id)),
                            Bet.period.in_(select(max_version_subquery.c.period)),
                            Bet.type.in_(select(max_version_subquery.c.type)),
                            Bet.version.in_(select(max_version_subquery.c.max_version))
                        )
                    )
                )
            )
        )

        async with async_session_factory() as session:
            res = await session.execute(delete_query)
            await session.commit()

            del_count = res.rowcount
            logger.info(f'Removed {del_count} objects from Bet')

