from src.parser.collector.straight import collect_content
from src.parser.collector.heads import collect_heads
from src.core.crud.parser.match import archive_and_clear_matches
from src.parser.config import sports

async def startup(ctx):
    await collect_heads(sports=sports)
    await collect_content()
    await archive_and_clear_matches()

async def get_heads(ctx):
    await collect_heads(sports=sports)

async def get_straight(ctx):
    await collect_content()

async def archive_matches(ctx):
    await archive_and_clear_matches()
