from src.core.db.db_helper import db_helper
from src.parser.config import sports
from src.services.parser_head_service import ParserHeadService
from src.services.parser_straight_service import ParserStraightService
from src.services.parser_archive_service import ParserArchiveService
from src.repositories.match_repository import MatchRepository

from src.core.logger import get_module_logger
logger = get_module_logger(__name__)

class StraightParserError(Exception):
    '''
    Straight Parser Error
    '''
    pass

async def startup(ctx):
    async with db_helper.session_factory() as session:
        await ParserArchiveService.archive_and_clear_matches(session=session)

    async with db_helper.session_factory() as session:
        await ParserHeadService.collect_heads(sports, session=session)

    async with db_helper.session_factory() as session:
        matches = await MatchRepository.get_upcoming_matches(session=session)
    
    await ParserStraightService.collect_content(matches=matches)

async def get_heads(ctx):
    try:
        async with db_helper.session_factory() as session:
            await ParserHeadService.collect_heads(sports, session=session)
    except Exception as e:
        logger.error(StraightParserError(e))


async def get_straight(ctx):
    try:
        async with db_helper.session_factory() as session:
            matches = await MatchRepository.get_upcoming_matches(session=session)
        await ParserStraightService.collect_content(matches=matches)
    except Exception as e:
        logger.error(StraightParserError(e))

async def archive_matches(ctx):
    async with db_helper.session_factory() as session:
        await ParserArchiveService.archive_and_clear_matches(session=session)
