import datetime
from collections import defaultdict
from datetime import timedelta


def justify_changes(changes: list, start_time: datetime):
    """             'old_home_cf': change[0],
                    'new_home_cf': change[1],
                    'old_away_cf': change[2],
                    'new_away_cf': change[3],
                    'old_point': change[4],
                    'new_point': change[5],
                    'type': change[6],
                    'period': change[7],
                    'created_at': change[8]
    """

    merged_change = {}
    for change in changes:
        key = (change['period'], change['type'].value)
        if key in merged_change:
            merged_change[key].append(change)
        else:
            merged_change[key] = []
            merged_change[key].append(change)

    for key in merged_change:
        result = []
        for obj in merged_change[key]:
            if obj['created_at'] + timedelta(hours=1) >= start_time:
                result.append(obj)
            elif obj['created_at'] + timedelta(hours=3) < start_time:
                pass


