import asyncio
import sys
from src.bot.bot import send_report

async def main():
    if len(sys.argv) > 1:
        try:
            match_id = int(sys.argv[1])
        except ValueError:
            print(f"Ошибка: аргумент должен быть числом, получено: {sys.argv[1]}")
            sys.exit(1)
    else:
        print("Ошибка: требуется указать ID матча")
        print("Использование: python3 -m src.commands.send_report <match_id>")
        sys.exit(1)
    
    await send_report(match_id)

if __name__ == "__main__":
    asyncio.run(main())