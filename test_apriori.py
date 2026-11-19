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

        exact_rule = Rule((3,), (1, 2), support=2, antecedent_support=3)
        rules_at_exact_threshold = generate_rules(result.supports, Fraction(2, 3))
        self.assertIsInstance(rules_at_exact_threshold, list)
        self.assertIn(exact_rule, rules_at_exact_threshold)

        rules_at_higher_threshold = generate_rules(result.supports, Fraction(67, 100))
        self.assertNotIn(exact_rule, rules_at_higher_threshold)

    def test_missing_subset_prunes_the_join(self):
        result = apriori([[1, 2], [1, 3]], 1)
        self.assertEqual(result.levels, [LevelStats(1, 3, 3), LevelStats(2, 3, 2)])

    def test_matches_exhaustive_search(self):
        random = Random(2222)
        items = range(6)
        subsets = {}
        for size in range(1, len(items) + 1):
            for itemset in combinations(items, size):
                subsets[itemset] = set(itemset)

        for trial in range(25):
            baskets = []
            for _ in range(trial % 10):
                basket = set()
                for item in items:
                    if random.choice((True, False)):
                        basket.add(item)
                baskets.append(basket)

            min_support = random.randint(1, 5)
            min_confidence = random.choice((Fraction(0), Fraction(2, 3), Fraction(1)))

            all_counts = {}
            expected_supports = {}
            for itemset, subset in subsets.items():
                count = 0
                for basket in baskets:
                    if subset.issubset(basket):
                        count += 1
                all_counts[itemset] = count
                if count >= min_support:
                    expected_supports[itemset] = count

            expected_rules = set()
            for antecedent, antecedent_items in subsets.items():
                for consequent, consequent_items in subsets.items():
                    if not antecedent_items.isdisjoint(consequent_items):
                        continue

                    union = tuple(sorted(antecedent_items.union(consequent_items)))
                    joint_support = all_counts[union]
                    if joint_support < min_support:
                        continue

                    antecedent_support = all_counts[antecedent]
                    confidence = Fraction(joint_support, antecedent_support)
                    if confidence >= min_confidence:
                        rule = Rule(antecedent, consequent, joint_support, antecedent_support)
                        expected_rules.add(rule)

            with self.subTest(trial=trial, support=min_support, confidence=min_confidence):
                result = apriori(baskets, min_support)
                actual_rules = generate_rules(result.supports, min_confidence)
                self.assertEqual(result.supports, expected_supports)
                self.assertCountEqual(actual_rules, expected_rules)


if __name__ == "__main__":
    unittest.main()
