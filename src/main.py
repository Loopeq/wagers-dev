from collector.collector import collect
from src.data.crud import create_tables
import asyncio
import json


async def main():
    # hours = 1 * 60 * 60
    # while True:
    #     await collect()
    #     await asyncio.sleep(hours)
    await create_tables()

if __name__ == "__main__":
    asyncio.run(main())

