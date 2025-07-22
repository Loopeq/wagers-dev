from datetime import datetime
from typing import List

from sqlalchemy import select

from src.core.schemas import BetAddDTO
from src.core.db.db_helper import db_helper
from src.core.models import Bet


async def insert_bets_basketball(bets: List[BetAddDTO], match_id: int):
    bet_created_at = datetime.utcnow()

    async with db_helper.session_factory() as session:
        existing_bets_dict = {}

        stmt = select(
            Bet.match_id,
            Bet.type,
            Bet.period,
            Bet.point,
            Bet.version
        ).where(
            Bet.match_id == match_id
        ).order_by(
            Bet.match_id, Bet.type, Bet.period, Bet.version.desc()
        ).distinct(
            Bet.match_id, Bet.type, Bet.period
        )

        result = await session.execute(stmt)
        existing_bets = result.all()

        for match_id, bet_type, period, point, version in existing_bets:
            key = (match_id, bet_type, period)
            existing_bets_dict[key] = (point, version)

        new_bets = []
        for bet in bets:
            key = (bet.match_id, bet.type, bet.period)

            if key in existing_bets_dict:
                last_point, last_version = existing_bets_dict[key]
                if last_point != bet.point:
                    new_bets.append(Bet(
                        match_id=bet.match_id,
                        point=bet.point,
                        limit=bet.max_limit,
                        home_cf=bet.home_cf,
                        away_cf=bet.away_cf,
                        type=bet.type,
                        period=bet.period,
                        key=bet.key,
                        created_at=bet_created_at,
                        version=last_version + 1
                    ))
            else:
                new_bets.append(Bet(
                    match_id=bet.match_id,
                    point=bet.point,
                    limit=bet.max_limit,
                    home_cf=bet.home_cf,
                    away_cf=bet.away_cf,
                    type=bet.type,
                    period=bet.period,
                    key=bet.key,
                    created_at=bet_created_at,
                    version=0
                ))

        if new_bets:
            session.add_all(new_bets)
            await session.commit()


async def insert_bets_tennis(bets: List[BetAddDTO]):
    bet_created_at = datetime.utcnow()

    async with db_helper.session_factory() as session:
        bet_ids = {bet.match_id for bet in bets}
        stmt = select(Bet).where(
            Bet.match_id.in_(bet_ids)
        ).order_by(
            Bet.match_id, Bet.type, Bet.period, Bet.version.desc()
        )

        result = await session.execute(stmt)
        existing_bets = result.scalars().all()

        existing_bets_dict = {}
        for bet in existing_bets:
            key = (bet.match_id, bet.type, bet.period)
            if key not in existing_bets_dict:
                existing_bets_dict[key] = bet

        new_bets = []
        for bet in bets:
            key = (bet.match_id, bet.type, bet.period)
            existing_bet = existing_bets_dict.get(key)

            if existing_bet:
                changes = (
                        abs(existing_bet.home_cf - bet.home_cf) >= 0.15 or
                        abs(existing_bet.away_cf - bet.away_cf) >= 0.15
                )

                if changes:
                    new_bets.append(Bet(
                        match_id=bet.match_id,
                        point=bet.point,
                        limit=bet.max_limit,
                        home_cf=bet.home_cf,
                        away_cf=bet.away_cf,
                        type=bet.type,
                        period=bet.period,
                        key=bet.key,
                        created_at=bet_created_at,
                        version=existing_bet.version + 1
                    ))
            else:
                new_bets.append(Bet(
                    match_id=bet.match_id,
                    point=bet.point,
                    limit=bet.max_limit,
                    home_cf=bet.home_cf,
                    away_cf=bet.away_cf,
                    type=bet.type,
                    period=bet.period,
                    key=bet.key,
                    created_at=bet_created_at,
                    version=0
                ))

        if new_bets:
            session.add_all(new_bets)
            await session.commit()


async def insert_bets_football(bets: List[BetAddDTO]):
    bet_created_at = datetime.utcnow()

    async with db_helper.session_factory() as session:
        bet_ids = {bet.match_id for bet in bets}
        stmt = select(Bet).where(
            Bet.match_id.in_(bet_ids)
        ).order_by(
            Bet.match_id, Bet.type, Bet.period, Bet.version.desc()
        )

        result = await session.execute(stmt)
        existing_bets = result.scalars().all()

        existing_bets_dict = {}
        for bet in existing_bets:
            key = (bet.match_id, bet.type, bet.period)
            if key not in existing_bets_dict:
                existing_bets_dict[key] = bet

        new_bets = []
        for bet in bets:
            key = (bet.match_id, bet.type, bet.period)
            existing_bet = existing_bets_dict.get(key)

            if existing_bet:
                changes = (
                        abs(existing_bet.home_cf - bet.home_cf) >= 0.15 or
                        abs(existing_bet.away_cf - bet.away_cf) >= 0.15
                )

                if changes:
                    new_bets.append(Bet(
                        match_id=bet.match_id,
                        point=bet.point,
                        limit=bet.max_limit,
                        home_cf=bet.home_cf,
                        away_cf=bet.away_cf,
                        type=bet.type,
                        period=bet.period,
                        key=bet.key,
                        created_at=bet_created_at,
                        version=existing_bet.version + 1
                    ))
            else:
                new_bets.append(Bet(
                    match_id=bet.match_id,
                    point=bet.point,
                    limit=bet.max_limit,
                    home_cf=bet.home_cf,
                    away_cf=bet.away_cf,
                    type=bet.type,
                    period=bet.period,
                    key=bet.key,
                    created_at=bet_created_at,
                    version=0
                ))

        if new_bets:
            session.add_all(new_bets)
            await session.commit()


def create_bet(match_id: int, bet: BetAddDTO, version: int, created_at: datetime) -> Bet:
    return Bet(
            match_id=match_id,
            point=bet.point,
            limit=bet.max_limit,
            home_cf=bet.home_cf,
            away_cf=bet.away_cf,
            type=bet.type,
            period=bet.period,
            version=version,
            key=bet.key,
            created_at=created_at
    )
