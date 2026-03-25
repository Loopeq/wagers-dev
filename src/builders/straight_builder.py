from src.core.utils import get_period_title
from src.scripts.bet_clusters import group_bets


class StraightBuilder:

    def __init__(self, match_id: int, child_id: int, sport_id: int):
        self.match_id = match_id
        self.child_id = child_id
        self.sport_id = sport_id

    def _relation(self, match_id: int):
        if match_id == self.match_id:
            return "parent"
        if match_id == self.child_id:
            return "child"

    def map_changes(self, changes: list[dict]):
        periods = {}
        mapped = []

        for change in changes:
            relation = self._relation(change["match_id"])
            if not relation:
                continue

            period_title = get_period_title(self.sport_id, change["key"], relation)

            key = (period_title, change["match_id"], change["key"])

            period = periods.setdefault(
                key,
                {
                    "title": period_title,
                    "match_id": change["match_id"],
                    "key": change["key"],
                    "changes_count": 0,
                },
            )

            period["changes_count"] += 1

            mapped.append(
                {
                    **change,
                    "relation_type": relation,
                    "period_title": period_title,
                }
            )


        grouped = group_bets(mapped)

        return grouped, list(periods.values())

    def map_comparison(self, comparison: dict):
        result = []

        for pair in comparison["comparison"]:
            mapped_pair = []

            for comp in pair:
                if not comp:
                    continue

                relation = self._relation(comp["match_id"])
                if not relation:
                    continue

                mapped_pair.append(
                    {
                        **comp,
                        "relation_type": relation,
                        "period_title": get_period_title(
                            self.sport_id, comp["key"], relation
                        ),
                    }
                )

            result.append(mapped_pair)

        return result
