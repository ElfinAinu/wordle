# Full vowel coverage: what it costs and what it buys

Universe: data/answers.txt (2309 answers). Coverage words: SOARE + CLINT + DUMPY.

A *branch* is the set of answers consistent with the vowel feedback. Every share names its own denominator: the branch's answer count.

## With all six vowels decided

Decided: aeiouy. No answer has zero of them (0), so the first vowel is always found. Exactly one shows in 29.4% of games.

| only this shows | answers | share | vowel repeats | consonant repeats | nothing repeats | next guess | left |
|---|---|---|---|---|---|---|---|
| A | 166 | 7.2% | 22.9% | 13.9% | 63.3% | SLANT | 6.27 |
| E | 166 | 7.2% | 69.3% | 7.8% | 22.9% | STEER | 4.8 |
| I | 125 | 5.4% | 12.0% | 24.0% | 64.0% | SKIRT | 5.75 |
| O | 124 | 5.4% | 40.3% | 12.9% | 46.8% | STOOL | 5.94 |
| U | 87 | 3.8% | 5.7% | 25.3% | 69.0% | CRUST | 3.97 |
| Y | 12 | 0.5% | 50.0% | 16.7% | 33.3% | GLYPH | 1.17 |

## The same read without U and Y decided

Decided: aeio (SOARE + CLINT). U and Y are still unknown, so each branch is larger.

| only this shows | answers | share | vowel repeats | next guess | left |
|---|---|---|---|---|---|
| A | 301 | 13.0% | 15.0% | SLANT | 12.08 |
| E | 301 | 13.0% | 45.8% | TERSE | 7.66 |
| I | 225 | 9.7% | 7.1% | SPILT | 10.67 |
| O | 259 | 11.2% | 24.7% | TRULY | 11.82 |

## What coverage costs

| opening | average guesses | worst case | six or fail |
|---|---|---|---|
| SOARE + CLINT | 3.6146 | 6 | 0.04% |
| SOARE + CLINT + DUMPY | 4.1953 | 6 | 0.48% |

A third coverage word costs 0.58 guesses a game on average. Both openings are continued by simulate_method's expected-candidates-minimising policy over data/answers.txt.
