"""Level-wise Apriori mining and association rule generation."""

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from pathlib import Path

Itemset = tuple[int, ...]


@dataclass(frozen=True)
class LevelStats:
    size: int
    candidates: int
    frequent: int


@dataclass(frozen=True)
class MiningResult:
    transaction_count: int
    supports: dict[Itemset, int]
    levels: list[LevelStats]


@dataclass(frozen=True)
class Rule:
    antecedent: Itemset
    consequent: Itemset
    support: int
    antecedent_support: int

    @property
    def confidence(self) -> Fraction:
        return Fraction(self.support, self.antecedent_support)


def read_transactions(path: Path) -> Iterator[Itemset]:
    """Read a basket of whitespace-separated integer IDs from each nonblank line."""
    with path.open(encoding="utf-8") as dataset:
        for line_number, line in enumerate(dataset, start=1):
            item_ids = line.split()
            if not item_ids:
                continue

            transaction = []
            try:
                for item_id in item_ids:
                    transaction.append(int(item_id))
            except ValueError as error:
                raise ValueError(
                    f"{path}:{line_number}: expected whitespace-separated integer item IDs"
                ) from error

            yield tuple(transaction)


def _join_and_prune(previous_frequent: set[Itemset], size: int) -> set[Itemset]:
    """Join equal prefixes, then require every immediate subset to be frequent."""
    itemsets_by_prefix: dict[Itemset, list[Itemset]] = {}
    for itemset in sorted(previous_frequent):
        prefix = itemset[:-1]
        if prefix not in itemsets_by_prefix:
            itemsets_by_prefix[prefix] = []
        itemsets_by_prefix[prefix].append(itemset)

    candidates = set()
    for prefix_group in itemsets_by_prefix.values():
        for left, right in combinations(prefix_group, 2):
            # Both itemsets share a prefix. Append the larger of their last items.
            candidate = left + (right[-1],)
            # A candidate cannot be frequent if any of its subsets is infrequent.
            all_subsets_frequent = True
            for subset in combinations(candidate, size - 1):
                if subset not in previous_frequent:
                    all_subsets_frequent = False
                    break

            if all_subsets_frequent:
                candidates.add(candidate)

    return candidates


def _count_candidates(
    baskets: list[Itemset], candidates: set[Itemset], size: int
) -> dict[Itemset, int]:
    # Drop items that cannot contribute to a candidate at this level.
    active_items = set()
    for candidate in candidates:
        for item in candidate:
            active_items.add(item)

    counts: dict[Itemset, int] = {}
    for basket in baskets:
        filtered_basket = []
        for item in basket:
            if item in active_items:
                filtered_basket.append(item)

        for subset in combinations(filtered_basket, size):
            if subset in candidates:
                counts[subset] = counts.get(subset, 0) + 1

    return counts


def _mine_level(
    baskets: list[Itemset],
    min_support: int,
    previous_frequent: set[Itemset],
    size: int,
    supports: dict[Itemset, int],
    levels: list[LevelStats],
) -> None:
    """Mine one level and then recurse with its frequent itemsets."""
    if not previous_frequent:
        return

    candidates = _join_and_prune(previous_frequent, size)
    if not candidates:
        return

    candidate_counts = _count_candidates(baskets, candidates, size)
    current_frequent = set()
    for itemset, count in candidate_counts.items():
        if count >= min_support:
            current_frequent.add(itemset)
            supports[itemset] = count

    levels.append(LevelStats(size, len(candidates), len(current_frequent)))

    # The next level only needs the frequent itemsets from this level.
    del candidates, candidate_counts
    _mine_level(baskets, min_support, current_frequent, size + 1, supports, levels)


def apriori(transactions: Iterable[Iterable[int]], min_support: int) -> MiningResult:
    """Return exact support counts for all nonempty itemsets meeting min_support."""
    if min_support < 1:
        raise ValueError("minimum support must be a positive transaction count")

    baskets = []
    singleton_counts: dict[int, int] = {}
    for transaction in transactions:
        # Count each item once per transaction and keep a consistent order.
        basket = tuple(sorted(set(transaction)))
        baskets.append(basket)
        for item in basket:
            singleton_counts[item] = singleton_counts.get(item, 0) + 1

    supports: dict[Itemset, int] = {}
    for item, count in singleton_counts.items():
        if count >= min_support:
            supports[(item,)] = count

    levels = [LevelStats(1, len(singleton_counts), len(supports))]
    frequent_singletons = set(supports)
    _mine_level(baskets, min_support, frequent_singletons, 2, supports, levels)

    return MiningResult(len(baskets), supports, levels)


def generate_rules(
    supports: Mapping[Itemset, int], min_confidence: Fraction
) -> list[Rule]:
    """Return the rules that meet the minimum confidence."""
    if not 0 <= min_confidence <= 1:
        raise ValueError("minimum confidence must be between 0 and 1")

    rules = []
    for itemset, joint_support in supports.items():
        # Split the frequent itemset into a nonempty antecedent and consequent.
        for antecedent_size in range(1, len(itemset)):
            for antecedent in combinations(itemset, antecedent_size):
                antecedent_support = supports[antecedent]
                confidence = Fraction(joint_support, antecedent_support)
                if confidence < min_confidence:
                    continue

                antecedent_items = set(antecedent)
                consequent_items = []
                for item in itemset:
                    if item not in antecedent_items:
                        consequent_items.append(item)

                rule = Rule(
                    antecedent=antecedent,
                    consequent=tuple(consequent_items),
                    support=joint_support,
                    antecedent_support=antecedent_support,
                )
                rules.append(rule)

    return rules
