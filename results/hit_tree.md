# Guess-3 tree after SOARE+CLINT, branched on hit count

A hit = a tested letter that shows green or yellow.

| Hits | Share | Patterns | Avg left | Max left | Strategy |
|---|---|---|---|---|---|
| 0 | 0.6% | 1 | 15.0 | 15 | Burn word |
| 1 | 4.5% | 19 | 5.4 | 16 | Split candidates |
| 2 | 20.4% | 133 | 3.5 | 23 | Guess candidate |
| 3 | 43.1% | 426 | 2.3 | 25 | Guess candidate |
| 4 | 26.9% | 420 | 1.5 | 9 | Guess candidate |
| 5 | 4.5% | 102 | 1.0 | 2 | Solved |

## 0 hits — Burn word

0.6% of games, 1 patterns, avg 15.0 candidates

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Guess 3 | Left |
|---|---|---|---|---|---|---|
| SOARE | XXXXX | CLINT | XXXXX | 15 | DUMPY | 1.4 |

## 1 hits — Split candidates

4.5% of games, 19 patterns, avg 5.4 candidates

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Guess 3 | Left |
|---|---|---|---|---|---|---|
| SOARE | XGXXX | CLINT | XXXXX | 16 | DEBUG | 1.88 |
| SOARE | XXYXX | CLINT | XXXXX | 15 | PUDGY | 1.27 |
| SOARE | XXXXX | CLINT | XXYXX | 10 | DUMPY | 1.4 |

## 2 hits — Guess candidate

20.4% of games, 133 patterns, avg 3.5 candidates

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Guess 3 | Left |
|---|---|---|---|---|---|---|
| SOARE | XXXYY | CLINT | XXXXX | 23 | DUMPY | 1.78 |
| SOARE | XXXXX | CLINT | XYYXX | 14 | DWELL | 1.86 |
| SOARE | XGXXX | CLINT | XYXXX | 14 | DALLY | 2.0 |

## 3 hits — Guess candidate

43.1% of games, 426 patterns, avg 2.3 candidates

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Guess 3 | Left |
|---|---|---|---|---|---|---|
| SOARE | XXYYY | CLINT | XXXXX | 25 | GAWKY | 3.48 |
| SOARE | XGXYY | CLINT | XXXXX | 14 | WIMPY | 3.14 |
| SOARE | XYYYX | CLINT | XXXXX | 12 | ARMOR | 1.5 |

## 4 hits — Guess candidate

26.9% of games, 420 patterns, avg 1.5 candidates

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Guess 3 | Left |
|---|---|---|---|---|---|---|
| SOARE | XXYYY | CLINT | XXXXY | 9 | MATCH | 1.44 |
| SOARE | XXYYY | CLINT | XYXXX | 9 | BAGGY | 1.22 |
| SOARE | XYYYX | CLINT | XXXYX | 6 | BAGGY | 1.0 |

## 5 hits — Solved

4.5% of games, 102 patterns, avg 1.0 candidates

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Guess 3 | Left |
|---|---|---|---|---|---|---|
| SOARE | YXYYG | CLINT | XXGXX | 2 | ABACK | 1.0 |
| SOARE | YXXYY | CLINT | XXYYX | 2 | ABBEY | 1.0 |
| SOARE | XYYGX | CLINT | YXXYX | 1 | ABACK | 1.0 |
