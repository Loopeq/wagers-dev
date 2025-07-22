from collections import defaultdict


def process_changes(bets: list[dict], sport_id: int, interval: int):
    bets = list(bets.__reversed__())
    return bets


def group_bets(mapped_changes: list[dict[str]]) -> list[list[dict[str]]]:
    grouped_changes = defaultdict(list)
    for change in mapped_changes:
        key = (change['period'], change['type'], change['relation_type'])
        grouped_changes[key].append(change)

    all_pairs = []
    for group in grouped_changes.values():
        sorted_group = sorted(group, key=lambda x: x['created_at'])

        pairs = [
            [sorted_group[i], sorted_group[i + 1]]
            for i in range(len(sorted_group) - 1)
        ]

        all_pairs.extend(pairs)

    all_pairs_sorted = sorted(
        all_pairs,
        key=lambda pair: pair[-1]['created_at'],
        reverse=True
    )

    return all_pairs_sorted

