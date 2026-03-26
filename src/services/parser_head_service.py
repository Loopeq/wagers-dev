import asyncio
from collections import defaultdict, deque
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import get_module_logger
from src.core.models import League, Match, Team
from src.parser.client.heads import get_heads
from src.core.utils import iso_to_utc
from src.repositories.match_repository import MatchRepository
from src.core.db.db_helper import db_helper

logger = get_module_logger(__name__)


class ParserHeadService:
    SKIP_CHILD_SPORTS = {"football"}

    @staticmethod
    def _is_future_prematch(event: dict, now: datetime) -> bool:
        return (
            event.get("type") == "matchup"
            and not event.get("isLive", False)
            and iso_to_utc(event["startTime"]) > now
        )

    @classmethod
    def _filter_events(
        cls,
        events: list[dict],
        sport_name: str,
        now: datetime,
    ) -> list[dict]:
        filtered = [event for event in events if cls._is_future_prematch(event, now)]
        event_by_id = {event["id"]: event for event in filtered}

        valid_events: list[dict] = []
        skip_children = sport_name.lower() in cls.SKIP_CHILD_SPORTS

        for event in filtered:
            parent = event.get("parent")

            if skip_children and parent:
                continue

            if parent and parent.get("id") not in event_by_id:
                continue

            valid_events.append(event)

        return valid_events

    @staticmethod
    def _sort_by_parent_dependency(events: list[dict]) -> list[dict]:
        if not events:
            return []

        event_by_id = {event["id"]: event for event in events}
        graph: dict[int, list[int]] = defaultdict(list)
        indegree: dict[int, int] = defaultdict(int)

        for event in events:
            match_id = event["id"]
            parent = event.get("parent")
            parent_id = parent.get("id") if isinstance(parent, dict) else None

            if parent_id and parent_id in event_by_id:
                graph[parent_id].append(match_id)
                indegree[match_id] += 1
            else:
                indegree[match_id] += 0

        queue = deque(match_id for match_id in event_by_id if indegree[match_id] == 0)
        sorted_ids: list[int] = []

        while queue:
            current_id = queue.popleft()
            sorted_ids.append(current_id)

            for child_id in graph[current_id]:
                indegree[child_id] -= 1
                if indegree[child_id] == 0:
                    queue.append(child_id)

        if len(sorted_ids) != len(event_by_id):
            return events

        return [event_by_id[match_id] for match_id in sorted_ids]

    @staticmethod
    def _build_match_entities(event: dict) -> tuple[League, Match, Team, Team]:
        match_id = event["id"]
        parent = event.get("parent")
        parent_id = parent.get("id") if isinstance(parent, dict) else None
        match_start_time = iso_to_utc(event["startTime"])

        league_data = event["league"]
        sport_data = league_data["sport"]
        participants = event["participants"]

        league = League(
            id=league_data["id"],
            sport_id=sport_data["id"],
            name=league_data["name"],
        )

        match = Match(
            id=match_id,
            parent_id=parent_id,
            league_id=league_data["id"],
            start_time=match_start_time,
        )

        team_home = Team(
            name=participants[0]["name"],
            league_id=league_data["id"],
        )

        team_away = Team(
            name=participants[1]["name"],
            league_id=league_data["id"],
        )

        return league, match, team_home, team_away

    @classmethod
    async def _process_event(
        cls,
        event: dict,
        existing_ids: set[int],
        session: AsyncSession,
    ) -> Match:
        match_id = event["id"]
        match_start_time = iso_to_utc(event["startTime"])

        league, match, team_home, team_away = cls._build_match_entities(event)

        if match_id in existing_ids:
            await MatchRepository.update_start_time(
                match_id=match_id,
                new_start_time=match_start_time,
                session=session,
            )
            return match
        await MatchRepository.add_match_cascade(
            league=league,
            match=match,
            team_home=team_home,
            team_away=team_away,
            session=session,
        )
        return match

    @classmethod
    async def collect_from_heads_data(
        cls,
        data: list[dict],
        sport_name: str,
        session: AsyncSession,
    ) -> list[Match]:
        now = datetime.utcnow()

        valid_events = cls._filter_events(
            events=data,
            sport_name=sport_name,
            now=now,
        )
        sorted_events = cls._sort_by_parent_dependency(valid_events)

        existing_ids = await MatchRepository.get_existing_ids(
            [event["id"] for event in sorted_events],
            session=session,
        )

        results: list[Match] = []

        for event in sorted_events:
            match_id = event["id"]
            try:
                async with db_helper.session_factory() as session:
                    async with session.begin():
                        match = await cls._process_event(
                            event=event,
                            existing_ids=existing_ids,
                            session=session,
                        )
                        results.append(match)
            except Exception as exc:
                logger.error(f"Process match error {match_id}: {exc}")
        return results

    @classmethod
    async def collect_heads(
        cls,
        sports: dict[str, int],
        session: AsyncSession,
    ) -> list[Match]:
        responses = await asyncio.gather(
            *(get_heads(event_id=sport_id) for sport_id in sports.values())
        )

        results: list[Match] = []

        for sport_name, response in zip(sports.keys(), responses):
            if response.status == 404:
                continue

            matches = await cls.collect_from_heads_data(
                data=response.data,
                sport_name=sport_name,
                session=session,
            )
            results.extend(matches)

        return results