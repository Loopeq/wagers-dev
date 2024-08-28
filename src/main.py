from downloader import run_downloader
import asyncio


async def main():
    await run_downloader()


if __name__ == "__main__":
    asyncio.run(main())
