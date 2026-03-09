import asyncio
from datetime import datetime
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import get_module_logger
from src.core.schemas import BetAddDTO, MatchUpcomingDTO
from src.core.utils import format_key
from src.parser.client.straight import get_straight
from src.parser.config import sports, sports_ids
from src.parser.utils.common import calc_coeff
from src.repositories.bet_repository import BetRepository
from src.scripts.bet_clusters import extract_latest, is_int_or_half

logger = get_module_logger(__name__)


class ParserStraightService:
    POINT_FILTER_SPORTS = {"football", "tennis"}
    TENNIS_CHILD_ALLOWED_KEYS = {"s;0;ou"}

    @classmethod
    async def collect_content(
        cls,
        matches: Iterable[MatchUpcomingDTO],
        session: AsyncSession,
    ) -> None:
        response_date = datetime.utcnow()

        tasks = [
            cls.process_match(match=match, response_date=response_date, session=session)
            for match in matches
            if match.sport_id in {
                sports["basketball"],
                sports["tennis"],
                sports["football"],
            }
        ]

        if tasks:
            await asyncio.gather(*tasks)

    @classmethod
    async def process_match(
        cls,
        match: MatchUpcomingDTO,
        response_date: datetime,
        session: AsyncSession,
    ) -> None:
        bets = await cls.extract_bet_content(
            match=match,
            response_date=response_date,
            session=session,
        )

        if not bets:
            return

        if match.sport_id == sports["basketball"]:
            await BetRepository.insert_bets_points(
                bets=bets,
                match_id=match.id,
                session=session,
            )
            return

        await BetRepository.insert_bets_coeffs(
            bets=bets,
            session=session,
        )

    @classmethod
    async def extract_bet_content(
        cls,
        match: MatchUpcomingDTO,
        response_date: datetime,
        session: AsyncSession,
    ) -> list[BetAddDTO]:
        content_response = await get_straight(match_id=match.id)

        if content_response.status == 404 or match.start_time < response_date:
            return []

        all_event_bets = await BetRepository.get_event_bets(
            match_id=match.id,
            session=session,
        )
        latest_bets = extract_latest(all_event_bets)

        bets: list[BetAddDTO] = []
        seen_bets: set[tuple] = set()

        for item in content_response.data:
            bet = cls._build_bet_dto(
                item=item,
                match=match,
                response_date=response_date,
                latest_bets=latest_bets,
                seen_bets=seen_bets,
            )
            if bet is not None:
                bets.append(bet)

        return bets

    @classmethod
    def _build_bet_dto(
        cls,
        item: dict,
        match: MatchUpcomingDTO,
        response_date: datetime,
        latest_bets: dict,
        seen_bets: set[tuple],
    ) -> BetAddDTO | None:
        matchup_id = item.get("matchupId")
        if matchup_id != match.id:
            return None

        bet_type = item.get("type")
        period = item.get("period")
        raw_key = item.get("key")

        if raw_key is None:
            return None

        key = cls._build_key(bet_type=bet_type, raw_key=raw_key)
        bet_key = (bet_type, period, key, matchup_id)

        prices = item.get("prices") or []
        if len(prices) < 2:
            return None

        point = prices[0].get("points")

        if not cls._is_bet_allowed(
            item=item,
            match=match,
            key=key,
            bet_key=bet_key,
            point=point,
            latest_bets=latest_bets,
            seen_bets=seen_bets,
        ):
            return None

        limits = item.get("limits") or []
        limit_max = limits[0].get("amount") if limits else None

        home_price = calc_coeff(prices[0]["price"])
        away_price = calc_coeff(prices[1]["price"])
        draw_price = calc_coeff(prices[2]["price"]) if len(prices) == 3 else None

        return BetAddDTO(
            match_id=match.id,
            point=point,
            max_limit=limit_max,
            home_cf=home_price,
            draw_cf=draw_price,
            away_cf=away_price,
            type=bet_type,
            period=period,
            key=key,
            created_at=response_date,
        )

    @classmethod
    def _build_key(cls, bet_type: str | None, raw_key: str) -> str:
        key = format_key(raw_key)

        if bet_type == "team_total":
            side = raw_key.split(";")[-1]
            key += side

        return key

    @classmethod
    def _is_bet_allowed(
        cls,
        item: dict,
        match: MatchUpcomingDTO,
        key: str,
        bet_key: tuple,
        point,
        latest_bets: dict,
        seen_bets: set[tuple],
    ) -> bool:
        sport_name = sports_ids.get(match.sport_id)

        if sport_name == "tennis" and match.parent_id and key not in cls.TENNIS_CHILD_ALLOWED_KEYS:
            return False

        if sport_name in cls.POINT_FILTER_SPORTS:
            return cls._handle_point_filtered_bet(
                key=key,
                bet_key=bet_key,
                point=point,
                latest_bets=latest_bets,
                seen_bets=seen_bets,
            )

        return cls._handle_regular_bet(
            item=item,
            bet_key=bet_key,
            seen_bets=seen_bets,
        )

    @staticmethod
    def _handle_point_filtered_bet(
        key: str,
        bet_key: tuple,
        point,
        latest_bets: dict,
        seen_bets: set[tuple],
    ) -> bool:
        if bet_key in seen_bets:
            return False

        if point is None:
            seen_bets.add(bet_key)
            return True

        if not is_int_or_half(point):
            return False

        latest = latest_bets.get(key)
        if latest and latest.point != point:
            return False

        seen_bets.add(bet_key)
        return True

    @staticmethod
    def _handle_regular_bet(
        item: dict,
        bet_key: tuple,
        seen_bets: set[tuple],
    ) -> bool:
        if item.get("isAlternate", True):
            return False

        if bet_key in seen_bets:
            return False

        seen_bets.add(bet_key)
        return True