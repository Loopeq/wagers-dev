from src.core.db.db_helper import db_helper
from src.core.crud.parser.match import archive_and_clear_matches
from src.parser.config import sports
from src.services.parser_head_service import ParserHeadService
from src.services.parser_straight_service import ParserStraightService
from src.services.parser_archive_service import ParserArchiveService
from src.repositories.match_repository import MatchRepository


async def startup(ctx):
    async with db_helper.session_factory() as session:
        await ParserHeadService.collect_heads(sports, session=session)

    async with db_helper.session_factory() as session:
        matches = await MatchRepository.get_upcoming_matches(session=session)
        await ParserStraightService.collect_content(matches=matches, session=session)

    async with db_helper.session_factory() as session:
        await ParserArchiveService.archive_and_clear_matches(session=session)


async def get_heads(ctx):
    async with db_helper.session_factory() as session:
        await ParserHeadService.collect_heads(sports, session=session)

async def get_straight(ctx):
    async with db_helper.session_factory() as session:
        matches = await MatchRepository.get_upcoming_matches(session=session)
        await ParserStraightService.collect_content(matches=matches, session=session)


async def archive_matches(ctx):
    async with db_helper.session_factory() as session:
        await ParserArchiveService.archive_and_clear_matches(session=session)
