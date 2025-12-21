import asyncio
import sys
from src.bot.bot import send_report

async def main():
    report_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    await send_report(report_id)

if __name__ == "__main__":
    asyncio.run(main())