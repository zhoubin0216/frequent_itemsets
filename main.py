"""Run Apriori on a transaction file and optionally export the complete result."""

import argparse
import json
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from time import perf_counter

from apriori import apriori, generate_rules, read_transactions

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
        if args.output is not None and args.output.resolve() == args.dataset.resolve():
            parser.error("output path must differ from the input dataset")

        start = perf_counter()
        result = apriori(read_transactions(args.dataset), args.min_support)
        mining_seconds = perf_counter() - start

        rules = []
        rules_seconds = None
        if args.min_confidence is not None:
            start = perf_counter()
            rules = list(generate_rules(result.supports, Fraction(args.min_confidence)))
            rules_seconds = perf_counter() - start

        print(f"Transactions: {result.transaction_count:,}")
        print(f"Minimum support: {args.min_support:,} transactions")
        print(f"{'Size':>4} {'Candidates':>12} {'Frequent':>12}")
        for level in result.levels:
            print(f"{level.size:>4} {level.candidates:>12,} {level.frequent:>12,}")
        print(f"Frequent itemsets: {len(result.supports):,}")
        print(f"Mining time (including input): {mining_seconds:.3f} s")
        top_itemsets = sorted(
            result.supports.items(), key=lambda pair: (-pair[1], len(pair[0]), pair[0])
        )
        for itemset, support in top_itemsets[:5]:
            print(f"  {itemset}  support={support}")

        if rules_seconds is not None:
            print(f"Rules at confidence >= {args.min_confidence}: {len(rules):,}")
            print(f"Rule generation time: {rules_seconds:.3f} s")
            rules.sort(
                key=lambda rule: (-rule.confidence, -rule.support, rule.antecedent, rule.consequent)
            )
            for rule in rules[:5]:
                print(
                    f"  {rule.antecedent} -> {rule.consequent}  "
                    f"support={rule.support}  confidence={float(rule.confidence):.6f}"
                )

        if args.output is not None:
            payload = {
                "dataset": args.dataset.name,
                "transaction_count": result.transaction_count,
                "min_support": args.min_support,
                "min_confidence": float(args.min_confidence)
                if args.min_confidence is not None
                else None,
                "levels": [asdict(level) for level in result.levels],
                "frequent_itemsets": [
                    {"items": items, "support": support}
                    for items, support in sorted(
                        result.supports.items(), key=lambda pair: (len(pair[0]), pair[0])
                    )
                ],
                "rules": [
                    {**asdict(rule), "confidence": float(rule.confidence)} for rule in rules
                ],
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"JSON output: {args.output}")
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
