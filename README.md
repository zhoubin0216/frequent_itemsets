# ID2222 Assignment 2 – Apriori

This Python project mines frequent itemsets and optionally generates association
rules. It uses the standard library and requires Python 3.9 or later.

## Dataset

To reproduce the evaluation, download `T10I4D100K.dat` and place it next to
`main.py`. [KTH course dataset](https://canvas.kth.se/courses/65339/files/10847690/download?wrap=1)

## Run in PyCharm

1. Choose **File → Open** and select the project folder.
2. Select a Python 3.9+ interpreter in the project's **Python Interpreter** settings.
3. Choose the **Apriori** run configuration and click **Run**. It uses the local
   `T10I4D100K.dat` file with a minimum support of 1,000 and a minimum confidence of 0.60.
4. To change the thresholds or export JSON, edit **Run → Edit Configurations → Apriori → Parameters**.

## Run from a terminal

Run the commands from the project directory.

```bash
# Frequent itemsets only
python3 main.py --min-support 1000

# Frequent itemsets and association rules, with full JSON output
python3 main.py T10I4D100K.dat --min-support 1000 --min-confidence 0.60 --output results/run.json

# Correctness tests
python3 -m unittest -v
```

The optional positional dataset argument defaults to `T10I4D100K.dat` next to
`main.py`. A dataset contains one basket of whitespace-separated integer item IDs
per nonblank line. Repeated IDs in a basket count once. Identical baskets on
different lines count as separate transactions.

`--min-support` takes a positive transaction count and defaults to 1,000.
`--min-confidence` takes a value from 0 to 1 and enables rule generation.
Both thresholds are inclusive. The console shows per-level counts, elapsed
time and up to five examples of each result type. `--output` saves every
frequent itemset and rule, with their support counts, to JSON.

[REPORT.md](REPORT.md) gives the algorithm and evaluation. The complete example
output is in [results/t10i4d100k_s1000_c060.json](results/t10i4d100k_s1000_c060.json).
