# Guess-3 tree after SOARE+CLINT, branched on hit count

A hit = a tested letter that shows green or yellow.
Candidates: 2,309 past answers (`data/answers.txt`).

**The rule:** Count your hits to find the candidate pool, then play the word that leaves the fewest expected candidates: a candidate if that word is still possible, otherwise a split word that reuses a hit letter or a burn word that carries no hit letter.

| Hits | Share | Patterns | Avg left | Max left | Actions in largest pools |
|---|---|---|---|---|---|
| 0 | 0.6% | 1 | 15.0 | 15 | Candidate |
| 1 | 4.5% | 19 | 5.4 | 16 | Burn word |
| 2 | 20.4% | 133 | 3.5 | 23 | Candidate, Split word |
| 3 | 43.1% | 426 | 2.3 | 25 | Candidate, Split word, Burn word |
| 4 | 26.9% | 420 | 1.5 | 9 | Candidate, Split word |
| 5 | 4.5% | 102 | 1.0 | 2 | Candidate |

## 0 hits

0.6% of games, 1 patterns, avg 15.0 candidates (largest pools shown, 1 of them)

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Action | Guess 3 | Left |
|---|---|---|---|---|---|---|---|
| SOARE | XXXXX | CLINT | XXXXX | 15 | Candidate | DUMPY | 1.4 |

## 1 hits

4.5% of games, 19 patterns, avg 5.4 candidates (largest pools shown, 3 of them)

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Action | Guess 3 | Left |
|---|---|---|---|---|---|---|---|
| SOARE | XGXXX | CLINT | XXXXX | 16 | Burn word | DEBUG | 1.88 |
| SOARE | XXYXX | CLINT | XXXXX | 15 | Burn word | PUDGY | 1.27 |
| SOARE | XXXXX | CLINT | XXYXX | 10 | Burn word | DUMPY | 1.4 |

## 2 hits

20.4% of games, 133 patterns, avg 3.5 candidates (largest pools shown, 3 of them)

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Action | Guess 3 | Left |
|---|---|---|---|---|---|---|---|
| SOARE | XXXYY | CLINT | XXXXX | 23 | Candidate | REEDY | 1.7 |
| SOARE | XGXXX | CLINT | XYXXX | 14 | Candidate | DOLLY | 2.0 |
| SOARE | XXXXX | CLINT | XYYXX | 14 | Split word | DWELL | 1.86 |

## 3 hits

43.1% of games, 426 patterns, avg 2.3 candidates (largest pools shown, 3 of them)

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Action | Guess 3 | Left |
|---|---|---|---|---|---|---|---|
| SOARE | XXYYY | CLINT | XXXXX | 25 | Split word | GAWKY | 3.48 |
| SOARE | XGXYY | CLINT | XXXXX | 14 | Burn word | WIMPY | 3.14 |
| SOARE | XXYXY | CLINT | XYXXX | 12 | Candidate | LEGAL | 1.33 |

## 4 hits

26.9% of games, 420 patterns, avg 1.5 candidates (largest pools shown, 3 of them)

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Action | Guess 3 | Left |
|---|---|---|---|---|---|---|---|
| SOARE | XXYYY | CLINT | XXXXY | 9 | Split word | MATCH | 1.44 |
| SOARE | XXYYY | CLINT | XYXXX | 9 | Candidate | RELAY | 1.22 |
| SOARE | XXXYY | CLINT | XXYYX | 6 | Candidate | DINER | 1.33 |

## 5 hits

4.5% of games, 102 patterns, avg 1.0 candidates (largest pools shown, 3 of them)

| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Action | Guess 3 | Left |
|---|---|---|---|---|---|---|---|
| SOARE | YXXYY | CLINT | XXYYX | 2 | Candidate | RESIN | 1.0 |
| SOARE | YXYYG | CLINT | XXGXX | 2 | Candidate | ARISE | 1.0 |
| SOARE | GGXXX | CLINT | YXYYX | 1 | Candidate | SONIC | 1.0 |
