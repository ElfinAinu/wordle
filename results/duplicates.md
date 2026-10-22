# Duplicate letters in the Wordle pools

| pool | words | any repeat | adjacent double | repeat a vowel apart |
|---|---|---|---|---|
| answers | 2309 | 32.4% | 14.7% | 10.3% |
| allowed-only | 12546 | 37.8% | 14.1% | 14.5% |
| all valid | 14855 | 37.0% | 14.2% | 13.9% |

## Distinct letters in the word (5 = no repeat)
| pool | 5 | 4 | 3 | 2 |
|---|---|---|---|---|
| answers | 67.6% | 29.8% | 2.5% | 0.0% |
| allowed-only | 62.2% | 33.5% | 4.2% | 0.1% |
| all valid | 63.0% | 33.0% | 3.9% | 0.1% |

## Repeat letter class: adjacent vs non-adjacent
Each repeated letter counted once per word. 'adjacent' is the share of that class whose copies touch; baseline is the class share of all letters in the pool.

| pool | kind | repeat instances | adjacent | baseline |
|---|---|---|---|---|
| answers | consonant | 422 (53.7%) | 52.6% | 60.9% |
| answers | vowel | 356 (45.3%) | 33.1% | 35.5% |
| answers | y | 8 (1.0%) | 0.0% | 3.7% |
| allowed-only | consonant | 2600 (50.5%) | 42.3% | 60.2% |
| allowed-only | vowel | 2503 (48.6%) | 27.2% | 36.7% |
| allowed-only | y | 45 (0.9%) | 0.0% | 3.2% |
| all valid | consonant | 3022 (50.9%) | 43.8% | 60.3% |
| all valid | vowel | 2859 (48.2%) | 27.9% | 36.5% |
| all valid | y | 53 (0.9%) | 0.0% | 3.2% |

## Over-representation among repeats (vs letter baseline)
| pool | vowel | consonant | y |
|---|---|---|---|
| answers | 1.28x (45.3% vs 35.5%) | 0.88x (53.7% vs 60.9%) | 0.27x (1.0% vs 3.7%) |
| allowed-only | 1.32x (48.6% vs 36.7%) | 0.84x (50.5% vs 60.2%) | 0.28x (0.9% vs 3.2%) |
| all valid | 1.32x (48.2% vs 36.5%) | 0.84x (50.9% vs 60.3%) | 0.28x (0.9% vs 3.2%) |

## Commonest repeated letters (adjacent or not)
- answers: E 172, O 81, L 71, A 69, T 61, R 60, S 49, C 29
- allowed-only: E 872, A 790, S 720, O 561, T 240, L 222, R 216, I 195
- all valid: E 1044, A 859, S 769, O 642, T 301, L 293, R 276, I 219

## Rare shapes (answers pool)
- Three or more copies of one letter: 20 (0.87%)
- Two independent pairs: 38 (1.6%)
- Repeated Y: 8 - coyly, dryly, gayly, gypsy, pygmy, shyly, slyly, wryly
