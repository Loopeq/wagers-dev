from collections import defaultdict

from src.core.models import Bet
from src.core.schemas import BetAddDTO


def process_changes(bets: list[dict]):
    bets = list(bets.__reversed__())
    return bets


def group_bets(mapped_changes: list[dict[str]]) -> list[list[dict[str]]]:
    grouped_changes = defaultdict(list)
    for change in mapped_changes:
        key = (change['period'], change['type'], change['relation_type'], change['key'])
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


def extract_latest(bets: list[Bet]):
    if not bets:
        return {}

    bet_key_mapper = {}
    for bet in sorted(bets, key=lambda bet: bet.version):
        bet_key_mapper[bet.key] = bet

    return bet_key_mapper


def is_int_or_half(number: int | float):
    return float(number * 2).is_integer()
