import asyncio
import requests


async def main():
    pass
    # headers = {
    #     'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    #     'X-Device-UUID': '6d702fee-ff3e303d-e0986d30-b379cb05',
    #     'sec-ch-ua-mobile': '?0',
    #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    #     'Content-Type': 'application/json',
    #     'Accept': 'application/json',
    #     'Referer': 'https://www.pinnacle.com/',
    #     'X-API-Key': 'CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R',
    #     'sec-ch-ua-platform': '"Linux"',
    # }
    # response = requests.get(
    #     'https://guest.api.arcadia.pinnacle.com/0.1/matchups/1595869339/markets/related/straight',
    #     headers=headers,
    #     proxies={'http': get_proxy()[0], 'https': get_proxy()[0]})
    # print(response.headers, response.request, response.text, response.content)


if __name__ == "__main__":
    asyncio.run(main())
