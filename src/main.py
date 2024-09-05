from collector.collector import collect
import asyncio
import json


async def main():
    hours = 1 * 60 * 60
    while True:
        await collect()
        await asyncio.sleep(hours)


if __name__ == "__main__":
    asyncio.run(main())

