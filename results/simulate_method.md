# Simulated performance of the taught fixed-opening method

Policy: play **SOARE**, then **CLINT**, then apply the guess-3 rule from `results/hit_tree.md` on every later turn.

> Count your hits to find the candidate pool, then play the word that leaves the fewest expected candidates: a candidate if that word is still possible, otherwise a split word that reuses a hit letter or a burn word that tests only fresh letters.

- Feedback: `hit_tree.pattern_codes` (standard greens-first Wordle feedback; each yellow consumes one answer copy).
- Guess words: data/answers.txt (2,309 words), the same pool hit_tree.py scores; data/allowed.txt was not used.
- Continuation: After guess 3 the same expected-candidates-minimising rule is applied each turn, excluding words already played.
- Substitutions: None: no stronger solver or candidate-only policy was substituted. Later guesses reuse the guess-3 rule rather than playing an exact optimal policy.

| Metric | Result |
|---|---|
| Games | 2309 |
| Average guesses | 3.61 |
| Worst case | 6 guesses |
| Solved on six or failed | 1 (0.04%) |
| Failed (not solved within 12) | 0 (0.00%) |

## Solve share by guess

| Guess | Solved | Share | Cumulative |
|---|---|---|---|
| 1 | 0 | 0.00% | 0.00% |
| 2 | 0 | 0.00% | 0.00% |
| 3 | 1004 | 43.48% | 43.48% |
| 4 | 1192 | 51.62% | 95.11% |
| 5 | 112 | 4.85% | 99.96% |
| 6 | 1 | 0.04% | 100.00% |
| Failed | 0 | 0.00% | 100.00% |

## Games needing six guesses or failing

| Answer | Guesses | Path |
|---|---|---|
| JOKER | 6 | SOARE XGXYY; CLINT XXXXX; WIMPY XXXXX; ROVER XGXGG; BOXER XGXGG; JOKER GGGGG |
