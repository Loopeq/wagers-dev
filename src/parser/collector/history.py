import asyncio
from typing import List, Optional, Dict

from src.core.db.db_helper import db_helper
from src.core.models import MatchResult
from src.parser.calls.event_details import get_match_details

from src.parser.calls.league import fetch


async def fetch_leagues() -> Optional[List[Dict]]:
    return await fetch()


def find_league_by_id(leagues: List[Dict], league_id: int) -> Optional[Dict]:
    return next((league for league in leagues if league['id'] == league_id), None)


def find_first_period_details(details: List[Dict]) -> Optional[Dict]:
    return next((detail for detail in details if detail['number'] == 0), None)


async def process_match(
    match: List[int],
    leagues: List[Dict],
    semaphore: asyncio.Semaphore,
    sleep_duration: float,
    result: List[MatchResult],
) -> None:
    async with semaphore:
        await asyncio.sleep(sleep_duration)
        match_id, league_id = match
        match_details = await get_match_details(match_id)

        period_details = find_first_period_details(match_details)
        league = find_league_by_id(leagues, league_id)

        if period_details and league:
            home_team_is_team1 = league.get('homeTeamType') == 'Team1'
            team_1_score = (
                period_details['team_1_score']
                if home_team_is_team1
                else period_details['team_2_score']
            )
            team_2_score = (
                period_details['team_2_score']
                if home_team_is_team1
                else period_details['team_1_score']
            )

            result.append(
                MatchResult(
                    match_id=match_id,
                    period=period_details['number'],
                    team_1_score=team_1_score,
                    team_2_score=team_2_score,
                )
            )


async def get_history_details(together: int = 10, sleep: float = 0.2) -> Optional[dict]:
    result: List[MatchResult] = []
    semaphore = asyncio.Semaphore(together)

    leagues = await fetch_leagues()
    if not leagues:
        return

    matches = await MatchOrm.get_matches_ready_to_results()
    if not matches:
        return

    tasks = [
        process_match(match, leagues, semaphore, sleep, result)
        for match in matches
    ]
    await asyncio.gather(*tasks)

    async with db_helper.session_factory() as session:
        session.add_all(result)
        await session.commit()

    return {"matches_processed": len(result)}
