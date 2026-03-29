from typing import Literal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.core.models import Bet
from src.core.schemas import BetAddDTO


class BetRepository:
    @staticmethod
    async def get_event_bets(match_id: int, session: AsyncSession):
        stmt = (
            select(Bet).where(Bet.match_id == match_id).order_by(Bet.created_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_bets_by_match_ids(
        match_ids: list[int],
        session: AsyncSession,
    ) -> list[Bet]:
        if not match_ids:
            return []

        stmt = select(Bet).where(Bet.match_id.in_(match_ids))
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_changes(
        match_ids: list[int | None],
        periods: list | None,
        session: AsyncSession,
    ) -> list[dict]:
        filtered_match_ids = [
            match_id for match_id in match_ids if match_id is not None
        ]

        stmt = select(Bet).where(Bet.match_id.in_(filtered_match_ids))

        if periods:
            stmt = stmt.where(Bet.key.in_(periods))

        stmt = stmt.order_by(Bet.created_at.desc())

        result = await session.execute(stmt)
        bets = result.scalars().all()
        return [
            {
                key: value
                for key, value in bet.__dict__.items()
                if key != "_sa_instance_state"
            }
            for bet in bets
        ]

    @staticmethod
    async def get_initial_last_points(
        match_id: int,
        child_id: int | None,
        session: AsyncSession,
    ) -> dict:
        match_ids = [match_id]
        if child_id is not None:
            match_ids.append(child_id)

        max_version_subq = (
            select(
                Bet.match_id.label("match_id"),
                Bet.period.label("period"),
                Bet.type.label("type"),
                Bet.key.label("key"),
                func.max(Bet.version).label("max_version"),
            )
            .where(
                Bet.match_id.in_(match_ids),
                Bet.version != 0,
            )
            .group_by(Bet.match_id, Bet.period, Bet.type, Bet.key)
            .subquery()
        )

        bet_alias = aliased(Bet)

        stmt = (
            select(bet_alias)
            .outerjoin(
                max_version_subq,
                and_(
                    bet_alias.match_id == max_version_subq.c.match_id,
                    bet_alias.period == max_version_subq.c.period,
                    bet_alias.type == max_version_subq.c.type,
                    bet_alias.key == max_version_subq.c.key,
                ),
            )
            .where(
                bet_alias.match_id.in_(match_ids),
                or_(
                    bet_alias.version == 0,
                    bet_alias.version == max_version_subq.c.max_version,
                ),
            )
            .order_by(
                bet_alias.match_id.asc(),
                bet_alias.type.asc(),
                bet_alias.period.asc(),
                bet_alias.key.asc(),
                bet_alias.version.asc(),
            )
        )

        result = await session.execute(stmt)
        bets = result.scalars().all()

        raw_bets = [
            {
                key: value
                for key, value in bet.__dict__.items()
                if key != "_sa_instance_state"
            }
            for bet in bets
        ]

        grouped = {}
        for bet in raw_bets:
            group_key = (bet["match_id"], bet["period"], bet["type"], bet["key"])
            grouped.setdefault(group_key, []).append(bet)

        comparison = []
        for bet_list in grouped.values():
            bet_list.sort(key=lambda item: item["version"])
            if len(bet_list) == 1:
                comparison.append((bet_list[0], None))
            else:
                comparison.append((bet_list[0], bet_list[-1]))

        return {"comparison": comparison}

    @staticmethod
    async def insert_bets(
        bets: list[BetAddDTO],
        session: AsyncSession,
        mode: Literal["coeffs", "points"],
    ) -> None:
        if not bets:
            return

        match_ids = list({bet.match_id for bet in bets})

        latest_subq = (
            select(
                Bet.match_id.label("match_id"),
                Bet.type.label("type"),
                Bet.period.label("period"),
                Bet.key.label("key"),
                func.max(Bet.version).label("max_version"),
            )
            .where(Bet.match_id.in_(match_ids))
            .group_by(Bet.match_id, Bet.type, Bet.period, Bet.key)
            .subquery()
        )

        stmt = select(Bet).join(
            latest_subq,
            and_(
                Bet.match_id == latest_subq.c.match_id,
                Bet.type == latest_subq.c.type,
                Bet.period == latest_subq.c.period,
                Bet.key == latest_subq.c.key,
                Bet.version == latest_subq.c.max_version,
            ),
        )

        result = await session.execute(stmt)
        latest_rows = result.scalars().all()

        latest_map: dict[tuple[int, str, int, str], Bet] = {
            (row.match_id, row.type, row.period, row.key): row for row in latest_rows
        }

        new_rows: list[Bet] = []

        for bet in bets:
            row_key = (bet.match_id, bet.type, bet.period, bet.key)
            latest = latest_map.get(row_key)

            if latest is None:
                new_row = Bet(
                    match_id=bet.match_id,
                    point=bet.point,
                    limit=bet.limit,
                    home_cf=bet.home_cf,
                    draw_cf=bet.draw_cf,
                    away_cf=bet.away_cf,
                    type=bet.type,
                    period=bet.period,
                    key=bet.key,
                    created_at=bet.created_at,
                    version=0,
                )
                new_rows.append(new_row)
                latest_map[row_key] = new_row
                continue

            if BetRepository._has_significant_change(latest=latest, new=bet, mode=mode):
                new_row = Bet(
                    match_id=bet.match_id,
                    point=bet.point,
                    limit=bet.limit,
                    home_cf=bet.home_cf,
                    draw_cf=bet.draw_cf,
                    away_cf=bet.away_cf,
                    type=bet.type,
                    period=bet.period,
                    key=bet.key,
                    created_at=bet.created_at,
                    version=latest.version + 1,
                )
                new_rows.append(new_row)
                latest_map[row_key] = new_row

        if new_rows:
            session.add_all(new_rows)

    @staticmethod
    def _has_significant_change(
        latest: Bet,
        new: BetAddDTO,
        mode: Literal["coeffs", "points"],
    ) -> bool:
        if mode == "points":
            return BetRepository._point_changed(latest.point, new.point, threshold=0.5)

        if mode == "coeffs":
            return any(
                [
                    BetRepository._num_changed(
                        latest.home_cf, new.home_cf, threshold=0.10
                    ),
                    BetRepository._num_changed(
                        latest.draw_cf, new.draw_cf, threshold=0.10
                    ),
                    BetRepository._num_changed(
                        latest.away_cf, new.away_cf, threshold=0.10
                    ),
                ]
            )

        return False

    @staticmethod
    def _point_changed(
        old: float | int | None, new: float | int | None, threshold: float
    ) -> bool:
        if old is None and new is None:
            return False
        if old is None or new is None:
            return True
        return abs(float(old) - float(new)) >= threshold

    @staticmethod
    def _num_changed(
        old: float | int | None, new: float | int | None, threshold: float
    ) -> bool:
        if old is None and new is None:
            return False
        if old is None or new is None:
            return True
        return abs(float(old) - float(new)) >= threshold
