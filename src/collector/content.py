import json
from pathlib import Path
import asyncio
from src.utils.common import calc_coeff
from json.decoder import JSONDecodeError


async def collect_straight_content(data: list[dict], header: dict) -> dict:
    result = []
    response_date = header.get('Date')
    for content in data:
        w_type = content['type']
        status = content.get('status')
        period = content.get('period')
        prices = content['prices']
        total_tmp = []
        for price in prices:
            design = price.get('designation')
            points = price.get('points')
            coeff = calc_coeff(price['price'])
            total_tmp.append({'design': design, 'points': points, 'coeff': coeff})
        info = {'w_type': w_type, 'status': status, 'period': period,
                'price': total_tmp}
        result.append(info)
    return {'content': result, 'response_date': response_date}


async def save_straight_content(data: dict, match_dir: Path):
    content_file = match_dir / 'content.json'
    tmp = []
    try:
        tmp = json.load(open(content_file))
        tmp.append(data)
    except (JSONDecodeError, FileNotFoundError):
        tmp = [data]
    finally:
        with open(content_file, 'w') as file:
            json.dump(tmp, file, indent=True, ensure_ascii=False)


