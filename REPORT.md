# Frequent Itemset Mining with Apriori

## Implementation

`apriori.py` normalizes each transaction into a sorted tuple of distinct IDs
and counts the single-item supports. At level \(k\), it joins frequent
\((k-1)\)-itemsets with the same first \(k-2\) items. It keeps a candidate only
if all of its \((k-1)\)-subsets were frequent. This pruning is valid because
every transaction containing an itemset also contains all of its subsets.
The program then scans the baskets, counts the candidate subsets present in
each basket, and keeps the candidates whose counts are at least the minimum
support \(s\). It stops when there are no more candidates or frequent itemsets.
[Agrawal and Srikant, VLDB 1994](https://www.vldb.org/conf/1994/P487.PDF)

For the bonus task, the program enumerates every nonempty proper subset
\(X\) of each frequent itemset \(F\) and sets the consequent to
\(Y = F \setminus X\). The rule has support \(\operatorname{supp}(F)\) and
confidence \(\operatorname{supp}(F)/\operatorname{supp}(X)\). Both counts are
already available from Apriori. The program compares the confidence with the
input threshold using exact integer arithmetic and emits the rule when the
threshold is met. This includes rules with multiple items on either side.

## Evaluation

I ran Python 3.9.6 on the supplied `T10I4D100K.dat` file, which contains
100,000 transactions and 870 distinct item IDs. All three runs used minimum
confidence 0.60. Mining time includes reading the dataset and running Apriori.
Each time is from one run and excludes rule generation and JSON output.

| Minimum support | Size 1 | Size 2 | Size 3 | Size 4 | Size 5 | Total itemsets | Rules | Mining time |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 500 | 569 | 342 | 110 | 43 | 9 | 1,073 | 1,072 | 16.716 s |
| 1,000 | 375 | 9 | 1 | 0 | 0 | 385 | 5 | 9.208 s |
| 2,000 | 155 | 0 | 0 | 0 | 0 | 155 | 0 | 3.971 s |

At support 1,000, the only frequent triple was `{39, 704, 825}`, with a support
of 1,035. The pair `{704, 825}` appeared in 1,102 transactions, so the rule
`{704, 825} → {39}` had confidence \(1035/1102 \approx 0.9392\).
The pair candidate count fell from 161,596 at support 500 to 70,125 at
support 1,000 and 11,935 at support 2,000 as fewer singletons qualified.

The unit tests compare all supports and rules with exhaustive enumeration
on 25 small datasets and cover duplicate IDs, candidate pruning and inclusive
thresholds. I also checked all three full-data runs with an independent
depth-first implementation that counted support by intersecting transaction ID
bit sets.
