# How Wordle repeats are shaped

Universe: data/answers.txt (2309 answers), 747 of them (32.4%) contain a repeat.
Opening pair: SOARE + CLINT (aceilnorst); the 10 letters it tests are the visibility reference.

A *repeat pair* is two copies of one letter; a letter used three times contributes three pairs. A *repeated-letter instance* is one repeated letter in one word, counted once however many copies it has.

## Slot pairs

Denominator: 826 repeat pairs.

| pair | count | share | touches |
|---|---|---|---|
| 3-4 | 198 | 24.0% | yes |
| 1-4 | 95 | 11.5% | no |
| 1-5 | 95 | 11.5% | no |
| 2-5 | 92 | 11.1% | no |
| 2-4 | 82 | 9.9% | no |
| 1-3 | 78 | 9.4% | no |
| 4-5 | 72 | 8.7% | yes |
| 2-3 | 68 | 8.2% | yes |
| 3-5 | 44 | 5.3% | no |
| 1-2 | 2 | 0.2% | yes |

## Shapes of a repeated letter

Denominator: 786 repeated-letter instances. Slots are 1-indexed positions in the answer.

| slots | count | touching |
|---|---|---|
| 3,4 | 186 | touching |
| 1,5 | 91 | separated |
| 2,5 | 87 | separated |
| 1,4 | 81 | separated |
| 2,4 | 80 | separated |
| 4,5 | 68 | touching |
| 2,3 | 66 | touching |
| 1,3 | 65 | separated |
| 3,5 | 41 | separated |
| 1,3,4 | 12 | touching |
| 1,4,5 | 2 | touching |
| 2,3,5 | 2 | touching |
| 2,4,5 | 2 | touching |
| 1,2 | 1 | touching |
| 1,2,5 | 1 | touching |
| 1,3,5 | 1 | separated |

## Touching vs separated, by letter class

Denominator: 786 repeated-letter instances (340 touching, 446 separated).

| kind | vowel | consonant | y |
|---|---|---|---|
| touching | 118 (34.7%) | 222 (65.3%) | 0 (0.0%) |
| separated | 238 (53.4%) | 200 (44.8%) | 8 (1.8%) |

## Visibility against the fixed opening

Denominator: 786 repeated-letter instances.

| opening tests the repeated letter | instances | share |
|---|---|---|
| yes | 639 | 81.3% |
| no | 147 | 18.7% |
