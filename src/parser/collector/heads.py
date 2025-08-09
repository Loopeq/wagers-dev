import asyncio
import datetime
import logging
from collections import defaultdict, deque
from src.requests.matchups import get_match_up_response
from src.core.models import League, Match, Team
from src.parser.utils.common import iso_to_utc
from src.core.crud.parser.match import check_exist, add_match_cascade


def accept_match_condition(event: dict, now_date: datetime.datetime) -> bool:
    return (
        event["type"] == "matchup"
        and not event["isLive"]
        and iso_to_utc(event["startTime"]) > now_date
    )


async def collect_heads_data(data: list[dict], sport_name: str):
    logging.info(f"Start collecting {len(data)} matches for {sport_name}")
    now_date = datetime.datetime.utcnow()

    filtered_events = [
        event for event in data
        if accept_match_condition(event, now_date)
    ]
    logging.info(f"{len(filtered_events)} из {len(data)} матчей прошли базовый фильтр")

    event_by_id = {event["id"]: event for event in filtered_events}

    valid_events = []
    skipped_due_to_parent = 0
    for event in filtered_events:
        parent = event.get("parent")

        # Исключаю все дочерний матчи для футбола и тениса
        if sport_name.lower() in ['football'] and parent:
            continue
        if parent and parent.get("id") not in event_by_id:
            skipped_due_to_parent += 1
            logging.warning(f"Матч {event['id']} пропущен — родитель {parent['id']} не найден в выборке")
            continue
        valid_events.append(event)

    logging.info(f"{len(valid_events)} матчей осталось после фильтрации родителей ({skipped_due_to_parent} пропущено)")

    event_by_id = {event["id"]: event for event in valid_events}
    existing_match_ids = await check_exist(list(event_by_id.keys()))

    graph = defaultdict(list)
    indegree = defaultdict(int)

    for event in valid_events:
        match_id = event["id"]
        parent = event.get("parent")
        parent_id = parent["id"] if parent and isinstance(parent, dict) and "id" in parent else None

        if parent_id and parent_id in event_by_id:
            graph[parent_id].append(match_id)
            indegree[match_id] += 1
        else:
            indegree[match_id] += 0

    queue = deque([match_id for match_id in event_by_id if indegree[match_id] == 0])
    sorted_ids = []

    while queue:
        current_id = queue.popleft()
        sorted_ids.append(current_id)
        for child_id in graph[current_id]:
            indegree[child_id] -= 1
            if indegree[child_id] == 0:
                queue.append(child_id)

    if len(sorted_ids) < len(event_by_id):
        skipped_ids = set(event_by_id) - set(sorted_ids)
        logging.warning(f"Циклическая зависимость между матчами. Пропущено {len(skipped_ids)} матчей: {skipped_ids}")

    inserted = 0
    for match_id in sorted_ids:
        event = event_by_id[match_id]
        try:
            inserted += await process_match(event, existing_match_ids)
        except Exception as e:
            logging.error(f"Ошибка при обработке матча {match_id}: {e}")

    logging.info(f"Finished collecting {inserted} matches for {sport_name}")


async def process_match(event: dict, existing_ids: list) -> int:
    match_id = event["id"]
    parent = event.get("parent")
    parent_id = parent["id"] if parent and isinstance(parent, dict) and "id" in parent else None

    if match_id in existing_ids:
        return 0

    league = event["league"]
    sport = league["sport"]
    participants = event["participants"]
    league_orm = League(id=league["id"], sport_id=sport["id"], name=league["name"])
    match_orm = Match(
        id=match_id,
        parent_id=parent_id,
        league_id=league["id"],
        start_time=iso_to_utc(event["startTime"])
    )
    team_home = Team(name=participants[0]["name"], league_id=league["id"])
    team_away = Team(name=participants[1]["name"], league_id=league["id"])

    await add_match_cascade(
        league=league_orm,
        match=match_orm,
        team_home=team_home,
        team_away=team_away
    )

    return 1


async def collect_heads(sports: dict[str, int]):
    responses = await asyncio.gather(
        *(get_match_up_response(event_id=sports[name]) for name in sports)
    )

    tasks = [
        collect_heads_data(resp.data, sport_name)
        for sport_name, resp in zip(sports.keys(), responses)
        if resp.status != 404
    ]

    if tasks:
        await asyncio.gather(*tasks)
