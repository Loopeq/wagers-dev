import asyncio
from src.data.crud import MatchOrm
from src.logs import logger
from src.parser.calls.league import fetch
from src.data.database import async_session_factory
from src.data.models import MatchResult
from src.parser.calls.event_details import get_match_details


async def get_history_details(together: int = 10, sleep: float = 0.2) -> dict | None:
    result: list = []
    sem = asyncio.Semaphore(together)

    leagues = await fetch()
    if not leagues:
        return

    matches = await MatchOrm.get_matches_ready_to_results()
    if not matches:
        return

    def check_order(leagues: list | None, l_id: int):
        order = list(filter(lambda x: x['id'] == l_id, leagues))
        if len(order):
            return order[0]
        return None

    def check_details(details: list | None):
        if details is None:
            return None
        details = list(filter(lambda x: x['number'] == 0, details))
        if len(details):
            return details[0]
        return None

    async def loop(match: list) -> None:
        async with sem:
            await asyncio.sleep(sleep)
            m_id, l_id = match[0], match[1]
            details = await get_match_details(m_id)
            checked_details = check_details(details)
            checked_order = check_order(leagues, l_id)

            if checked_details and checked_order:
                if checked_order.get('homeTeamType') == 'Team1':
                    team_1_score = checked_details['team_1_score']
                    team_2_score = checked_details['team_2_score']
                else:
                    team_1_score = checked_details['team_2_score']
                    team_2_score = checked_details['team_1_score']
                result.append(
                    MatchResult(
                        match_id=m_id,
                        period=checked_details.get('number'),
                        team_1_score=team_1_score,
                        team_2_score=team_2_score,
                    )
                )

    loops = [loop(match) for match in matches]
    await asyncio.gather(*loops)

    async with async_session_factory() as session:
        session.add_all(result)
        await session.commit()
        logger.info(f'Finish collecting history for {len(result)} matches')
