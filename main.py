"""Run Apriori on a transaction file and optionally export the complete result."""

import argparse
import json
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from time import perf_counter

from apriori import Itemset, MiningResult, Rule, apriori, generate_rules, read_transactions

DEFAULT_DATASET = Path(__file__).resolve().with_name("T10I4D100K.dat")


def positive_support(value: str) -> int:
    try:
        support = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a positive integer") from None
    if support < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return support


def confidence_threshold(value: str) -> Decimal:
    try:
        confidence = Decimal(value)
    except InvalidOperation:
        raise argparse.ArgumentTypeError("expected a number between 0 and 1") from None
    if not confidence.is_finite() or not 0 <= confidence <= 1:
        raise argparse.ArgumentTypeError("expected a number between 0 and 1")
    return confidence


def itemset_preview_order(entry: tuple[Itemset, int]) -> tuple[int, int, Itemset]:
    itemset, support = entry
    # Sort larger support counts first, then break ties by size and item IDs.
    return -support, len(itemset), itemset


def itemset_export_order(entry: tuple[Itemset, int]) -> tuple[int, Itemset]:
    itemset, _ = entry
    return len(itemset), itemset


def rule_output_order(rule: Rule) -> tuple[Fraction, int, Itemset, Itemset]:
    # Sort confidence and support from highest to lowest.
    return -rule.confidence, -rule.support, rule.antecedent, rule.consequent


def print_itemset_summary(
    result: MiningResult, min_support: int, mining_seconds: float
) -> None:
    print(f"Transactions: {result.transaction_count:,}")
    print(f"Minimum support: {min_support:,} transactions")
    print(f"{'Size':>4} {'Candidates':>12} {'Frequent':>12}")
    for level in result.levels:
        print(f"{level.size:>4} {level.candidates:>12,} {level.frequent:>12,}")
    print(f"Frequent itemsets: {len(result.supports):,}")
    print(f"Mining time (including input): {mining_seconds:.3f} s")

    top_itemsets = sorted(result.supports.items(), key=itemset_preview_order)
    for itemset, support in top_itemsets[:5]:
        print(f"  {itemset}  support={support}")


def print_rule_summary(
    rules: list[Rule], min_confidence: Decimal, rules_seconds: float
) -> None:
    print(f"Rules at confidence >= {min_confidence}: {len(rules):,}")
    print(f"Rule generation time: {rules_seconds:.3f} s")
    for rule in rules[:5]:
        confidence = float(rule.confidence)
        print(
            f"  {rule.antecedent} -> {rule.consequent}  "
            f"support={rule.support}  confidence={confidence:.6f}"
        )


def save_results(args: argparse.Namespace, result: MiningResult, rules: list[Rule]) -> None:
    level_rows = []
    for level in result.levels:
        level_rows.append({
            "size": level.size,
            "candidates": level.candidates,
            "frequent": level.frequent,
        })

    itemset_rows = []
    sorted_itemsets = sorted(result.supports.items(), key=itemset_export_order)
    for itemset, support in sorted_itemsets:
        itemset_rows.append({"items": itemset, "support": support})

    rule_rows = []
    for rule in rules:
        rule_rows.append({
            "antecedent": rule.antecedent,
            "consequent": rule.consequent,
            "support": rule.support,
            "antecedent_support": rule.antecedent_support,
            "confidence": float(rule.confidence),
        })

    min_confidence = None
    min_confidence_exact = None
    if args.min_confidence is not None:
        min_confidence = float(args.min_confidence)
        min_confidence_exact = str(args.min_confidence)

    payload = {
        "dataset": args.dataset.name,
        "transaction_count": result.transaction_count,
        "min_support": args.min_support,
        "min_confidence": min_confidence,
        "min_confidence_exact": min_confidence_exact,
        "levels": level_rows,
        "frequent_itemsets": itemset_rows,
        "rules": rule_rows,
    }

    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(payload, indent=2)
    output_path.write_text(json_text + "\n", encoding="utf-8")
    print(f"JSON output: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, nargs="?", default=DEFAULT_DATASET)
    parser.add_argument(
        "--min-support",
        type=positive_support,
        default=1000,
        help="minimum number of transactions containing an itemset (default: 1000)",
    )
    parser.add_argument(
        "--min-confidence",
        type=confidence_threshold,
        help="enable rules and set their minimum confidence from 0 to 1",
    )
    parser.add_argument("--output", type=Path, help="write all frequent itemsets and rules to JSON")
    args = parser.parse_args()

    try:
        if args.output is not None:
            same_file = args.output.resolve() == args.dataset.resolve()
            if not same_file and args.output.exists():
                same_file = args.output.samefile(args.dataset)
            if same_file:
                parser.error("output path must differ from the input dataset")

        start = perf_counter()
        transactions = read_transactions(args.dataset)
        result = apriori(transactions, args.min_support)
        mining_seconds = perf_counter() - start
        print_itemset_summary(result, args.min_support, mining_seconds)

        rules = []
        if args.min_confidence is not None:
            start = perf_counter()
            min_confidence = Fraction(args.min_confidence)
            rules = list(generate_rules(result.supports, min_confidence))
            rules_seconds = perf_counter() - start
            rules.sort(key=rule_output_order)
            print_rule_summary(rules, args.min_confidence, rules_seconds)

        if args.output is not None:
            save_results(args, result, rules)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
