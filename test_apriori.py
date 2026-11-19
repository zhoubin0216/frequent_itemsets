"""Compare Apriori with exhaustive counts on small baskets."""

import unittest
from fractions import Fraction
from itertools import combinations
from random import Random

from apriori import LevelStats, Rule, apriori, generate_rules


class AprioriTests(unittest.TestCase):
    def test_duplicate_items_repeated_baskets_and_inclusive_thresholds(self):
        baskets = [[3, 2, 1, 1], [1, 2, 3], [1, 2], [1, 3], [2]]
        result = apriori(baskets, 2)
        self.assertEqual(result.transaction_count, 5)
        self.assertEqual(
            result.supports,
            {
                (1,): 4,
                (2,): 4,
                (3,): 3,
                (1, 2): 3,
                (1, 3): 3,
                (2, 3): 2,
                (1, 2, 3): 2,
            },
        )

        rules = set(generate_rules(result.supports, Fraction(2, 3)))
        exact = Rule((3,), (1, 2), support=2, antecedent_support=3)
        self.assertIn(exact, rules)
        self.assertNotIn(exact, set(generate_rules(result.supports, Fraction(67, 100))))

    def test_missing_subset_prunes_the_join(self):
        result = apriori([[1, 2], [1, 3]], 1)
        self.assertEqual(result.levels, [LevelStats(1, 3, 3), LevelStats(2, 3, 2)])

    def test_matches_exhaustive_search(self):
        random = Random(2222)
        items = range(6)
        subsets = {
            subset: frozenset(subset)
            for size in range(1, 7)
            for subset in combinations(items, size)
        }

        for trial in range(25):
            baskets = [
                {item for item in items if random.choice((True, False))}
                for _ in range(trial % 10)
            ]
            support = random.randint(1, 5)
            confidence = random.choice((Fraction(0), Fraction(2, 3), Fraction(1)))
            all_counts = {
                items: sum(subset <= basket for basket in baskets)
                for items, subset in subsets.items()
            }
            expected_supports = {items: count for items, count in all_counts.items()
                                 if count >= support}
            expected_rules = set()
            for antecedent, antecedent_items in subsets.items():
                for consequent, consequent_items in subsets.items():
                    if antecedent_items.isdisjoint(consequent_items):
                        union = tuple(sorted(antecedent_items | consequent_items))
                        joint = all_counts[union]
                        if joint >= support and Fraction(joint, all_counts[antecedent]) >= confidence:
                            expected_rules.add(
                                Rule(antecedent, consequent, joint, all_counts[antecedent])
                            )

            with self.subTest(trial=trial, support=support, confidence=confidence):
                result = apriori(baskets, support)
                self.assertEqual(result.supports, expected_supports)
                self.assertCountEqual(generate_rules(result.supports, confidence), expected_rules)


if __name__ == "__main__":
    unittest.main()
