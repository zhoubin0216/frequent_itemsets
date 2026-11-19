"""Level-wise Apriori mining and association rule generation."""

from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, groupby
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
            items = line.split()
            if items:
                try:
                    yield tuple(map(int, items))
                except ValueError as error:
                    raise ValueError(
                        f"{path}:{line_number}: expected whitespace-separated integer item IDs"
                    ) from error


def _join_and_prune(previous: set[Itemset], size: int) -> set[Itemset]:
    """Join equal prefixes, then require every immediate subset to be frequent."""
    candidates = set()
    for _, group in groupby(sorted(previous), key=lambda itemset: itemset[:-1]):
        for left, right in combinations(group, 2):
            candidate = (*left, right[-1])
            if all(subset in previous for subset in combinations(candidate, size - 1)):
                candidates.add(candidate)
    return candidates


def _count_candidates(
    baskets: list[Itemset], candidates: set[Itemset], size: int
) -> Counter[Itemset]:
    active_items = {item for candidate in candidates for item in candidate}
    counts: Counter[Itemset] = Counter()
    for basket in baskets:
        filtered = tuple(item for item in basket if item in active_items)
        for subset in combinations(filtered, size):
            if subset in candidates:
                counts[subset] += 1
    return counts


def apriori(transactions: Iterable[Iterable[int]], min_support: int) -> MiningResult:
    """Return exact support counts for all nonempty itemsets meeting min_support."""
    if min_support < 1:
        raise ValueError("minimum support must be a positive transaction count")

    baskets = []
    singleton_counts: Counter[int] = Counter()
    for transaction in transactions:
        basket = tuple(sorted(set(transaction)))
        baskets.append(basket)
        singleton_counts.update(basket)

    supports = {
        (item,): count for item, count in singleton_counts.items() if count >= min_support
    }
    levels = [LevelStats(1, len(singleton_counts), len(supports))]
    previous = set(supports)
    size = 2
    while previous:
        candidates = _join_and_prune(previous, size)
        if not candidates:
            break

        counts = _count_candidates(baskets, candidates, size)
        frequent = {itemset: count for itemset, count in counts.items() if count >= min_support}
        levels.append(LevelStats(size, len(candidates), len(frequent)))
        supports.update(frequent)
        previous = set(frequent)
        size += 1

    return MiningResult(len(baskets), supports, levels)


def generate_rules(
    supports: Mapping[Itemset, int], min_confidence: Fraction
) -> Iterator[Rule]:
    """Generate rules from Apriori's complete table of frequent itemset supports."""
    if not 0 <= min_confidence <= 1:
        raise ValueError("minimum confidence must be between 0 and 1")

    for itemset, support in supports.items():
        for size in range(1, len(itemset)):
            for antecedent in combinations(itemset, size):
                antecedent_support = supports[antecedent]
                if support * min_confidence.denominator >= (
                    antecedent_support * min_confidence.numerator
                ):
                    antecedent_items = set(antecedent)
                    consequent = tuple(item for item in itemset if item not in antecedent_items)
                    yield Rule(antecedent, consequent, support, antecedent_support)
