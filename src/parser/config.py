import json
from pathlib import Path

current_file_path = Path(__file__).resolve()
current_dir = current_file_path.parent.parent.parent

config_path = current_dir / 'scaner-config.json'

with open(config_path, 'r') as file:
    config = json.loads(file.read())

sports = config['sports']
parse_content = config["parse_content"]
parse_allow_types = config["parse_allow_types"]
parse_headers = config["parse_headers"]
parse_results = config["parse_results"]
clean_changes_d = config["clean_changes_d"]
clean_matches_d = config["clean_matches_d"]
accuracy = config['accuracy']
accuracy_hour = accuracy['hour']
accuracy_far = accuracy['far']
accuracy_near = accuracy['near']
