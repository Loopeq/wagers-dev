import json
from pathlib import Path

current_file_path = Path(__file__).resolve()
current_dir = current_file_path.parent.parent.parent

config_path = current_dir / 'scaner-config.json'

with open(config_path, 'r') as file:
    config = json.loads(file.read())

sports = config['sports']
sports_ids = {value: key for key, value in sports.items()}
sports_ru = config['sports_ru']
parse_headers = config["parse_headers"]
parse_results = config["parse_results"]
clear_threshold = config["clear_threshold"]
clear_interval = config["clear_interval"]
tennis_threshold = config["tennis_threshold"]


