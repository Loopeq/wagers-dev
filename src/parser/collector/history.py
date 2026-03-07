from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from src.requests.results import get_history_events
from datetime import datetime, timezone
from src.core.db.db_helper import db_helper
from src.core.models import Match, MatchMember, Team, MatchResult, League
from sqlalchemy.orm import aliased
from sqlalchemy import cast, Date
from src.core.logger import get_module_logger
from src.core.utils import get_yesterday_ymd


logger = get_module_logger(__name__)


def timestamp_to_datetime(ms_timestamp: int) -> datetime:
    return datetime.fromtimestamp(ms_timestamp / 1000, tz=timezone.utc)


async def save_history():
    date = get_yesterday_ymd()
    response = await get_history_events(date=date)
    _, _, events, _ = response.data
    async with db_helper.session_factory() as session:
        for league in events:
            league_name, league_events = league[0], league[1]

            for match_event in league_events:
                home_name, away_name, start_ts, period, _, _, scores_dict, *_ = (
                    match_event
                )
                if "Games" in home_name or "Games" in away_name:
                    home_name = home_name.replace("(Games)", "").strip()
                    away_name = away_name.replace("(Games)", "").strip()
                else:
                    continue
                home_team = aliased(Team)
                away_team = aliased(Team)
                stmt = (
                    select(Match.id)
                    .join(League, League.id == Match.league_id)
                    .join(MatchMember, MatchMember.match_id == Match.id)
                    .join(home_team, home_team.id == MatchMember.home_id)
                    .join(away_team, away_team.id == MatchMember.away_id)
                    .filter(
                        League.name == league_name,
                        cast(Match.start_time, Date)
                        == timestamp_to_datetime(start_ts).date(),
                        home_team.name == home_name,
                        away_team.name == away_name,
                    )
                )
                expected_match_id = await session.execute(stmt)
                match_id = expected_match_id.scalar_one_or_none()

                if match_id is None:
                    continue

                for idx, score in scores_dict.items():
                    if int(idx) not in [0, 1, 2, 3, 4, 5]:
                        continue
                    if "-" in score:
                        t1, t2 = score.split("-")
                        try:
                            t1, t2 = int(t1), int(t2)
                        except ValueError:
                            continue
                    else:
                        continue

                    insert_stmt = (
                        insert(MatchResult)
                        .values(
                            match_id=match_id,
                            period=int(idx),
                            description=f"Game {idx}",
                            team_1_score=t1,
                            team_2_score=t2,
                        )
                        .on_conflict_do_nothing(index_elements=["match_id", "period"])
                    )
                    await session.execute(insert_stmt)

        await session.commit()
