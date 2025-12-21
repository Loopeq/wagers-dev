from src.requests.base import get_request
from src.parser.utils.proxy import ProxyManager
from playwright.async_api import async_playwright
from src.core.logger import get_module_logger
import asyncio
from pathlib import Path 
from src.core.settings import settings

playwright_path = Path('playwright/')
playwright_path.mkdir(exist_ok=True)
playwright_auth = playwright_path / '.auth'
playwright_auth.touch(exist_ok=True)

logger = get_module_logger(__name__)


async def _get_xdata():
    pm = ProxyManager()
    async with async_playwright() as p:
        proxy = pm.proxy_object
        browser = await p.chromium.launch(proxy={
            "server": proxy['server'],
            "username": proxy['username'],
            "password": proxy['password']
        })
        page = await browser.new_page()
        page.set_default_navigation_timeout(5000)
        await page.goto("https://www.pinnacle888.com/", wait_until="networkidle")
        await page.locator("[name='loginId']").fill(settings.PINNACLE_LOG)
        await page.locator("[name='pass']").fill(settings.PINNACLE_PASS)
        await page.locator("button[type='submit']", has_text="Sign In").click()

        await page.wait_for_load_state("networkidle")

        ulp_cookie = None
        for _ in range(15):
            cookies = await page.context.cookies()
            ulp_cookie = next((c for c in cookies if c['name'] == '_ulp'), None)
            if ulp_cookie:
                break
            await asyncio.sleep(1)
        
        if not ulp_cookie:
            raise Exception('No ulp cookie found.')

        await browser.close()

        return ulp_cookie

async def _get_results(date: str, xapp: str):
    headers = {
        'accept': '*/*',
        'accept-language': 'ru,ru-RU;q=0.9,en-US;q=0.8,en;q=0.7',
        'priority': 'u=1, i',
        'referer': 'https://www.pinnacle888.com/en/account/results',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'x-app-data': xapp 
    }
    params = {
        'sp': '33',
        'o': 'LEAGUE',
        'd': date,
        'locale': 'en_US',
    }


    response = await get_request(
        url='https://www.pinnacle888.com/member-service/v2/results/events',
        params=params,
        headers=headers,
    )

    if response.status != 200:
        raise Exception('Error fetching www.pinnacle888.com')
    return response


async def get_history_events(date: str, sport_id: int = 33, max_rtr: int = 10):
    with open(playwright_auth, 'r+') as auth:
        xdata = ','.join(field.rstrip('\n') for field in auth)
        if not xdata:
            xdata_request = await _get_xdata()
            xdata = f'{xdata_request["name"]}={xdata_request["value"]}'
            auth.seek(0)
            auth.write(xdata + '\n')
            auth.truncate()         
    for _ in range(max_rtr):
        try:
            response = await _get_results(date=date, xapp=xdata)
            return response
        except Exception as e:
            playwright_auth.unlink(missing_ok=True)
            logger.error(e)
        await asyncio.sleep(3)
