import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'


async def collect_match_headers(data: list[dict]) -> list[dict]:

    headers = []

    for event in data:

        match_id = event['id']
        start_time = event['startTime']
        league = event['league']
        league_name = league['name']
        sport = league['sport']
        sport_name = sport['name']
        sport_id = sport['id']
        participants = event['participants']
        home_team = participants[0]
        away_team = participants[1]
        home_name = home_team['name']
        away_name = away_team['name']

        header = {'match_id': match_id,
                  'start_time': start_time,
                  'league_name': league_name,
                  'sport_id': sport_id,
                  'sport_name': sport_name,
                  'home_name': home_name,
                  'away_name': away_name,
                  }
        headers.append(header)

    return headers


def save_match_header(header: dict):
    sport_dir = DATA_DIR / header['sport_name'].lower()
    sport_dir.mkdir(exist_ok=True)
    match_dir = sport_dir / str(header['match_id'])
    match_dir.mkdir(exist_ok=True)

    header_file = match_dir / 'head.json'

    if header_file.exists():
        return

    with open(header_file, 'w') as file:
        json.dump(header, file)
