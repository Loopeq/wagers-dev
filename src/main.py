import asyncio

from src.parser import run_parser
from src.api.server import run_server


async def main():
    parser_task = asyncio.create_task(run_parser())
    server_task = asyncio.create_task(run_server())

    await asyncio.gather(server_task, parser_task)


if __name__ == "__main__":
    asyncio.run(main())
