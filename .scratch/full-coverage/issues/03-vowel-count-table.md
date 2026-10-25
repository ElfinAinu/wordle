# 03: Section IX - the vowel-count table

**What to build:** A fourth figure in section IX, below the rule and cost cards:
how many vowels a word carries, across both pools.

The section's branch chart covers the single-vowel read. This figure supplies
the a-priori shape it sits inside — two vowels is the norm, so the six branches
above account for the 29.4% of games that show only one.

- **Fig. 10** — a `dtable` with a row per vowel count (0 through 4) plus a `3+`
  roll-up, and a column per pool: the 2,309 answers and all 14,855 valid words
  (answers plus the 12,546 allowed guesses), counted over A E I O U.
- A card beside it for the Y convention, since section IX is the Y-inclusive
  section: 3 or more is 14.9% of answers (16.6% of valid words) once Y counts,
  and no answer is then left without a vowel at all — the fact the section's
  opening claim rests on.

Both pools belong on the poster here. The answers pool is what the reader is
looking for; the valid pool is what they may play, and a coverage word is chosen
from it. The two differ enough to be worth showing: 9.9% of answers carry three
or more vowels against 11.3% of valid words.

**Blocked by:** 01 (measurement), 02 (section exists)

**Status:** done

- [x] `full_coverage.py` measures the distribution for both pools under both
      counting conventions, and writes it to `results/full_coverage.{json,md}`.
- [x] Fig. 10 appears in section IX with a row per vowel count and a 3+ roll-up,
      one column per pool.
- [x] The Y card states the answers and valid-pool figures for 3 or more, and
      that no answer is left vowel-less.
- [x] Every share names its denominator: the two pool sizes and the 12,546
      allowed guesses, not section IX's branch sizes or section VIII's counts.
- [x] The acceptance check re-derives every cell from `data/answers.txt` and
      `data/allowed.txt`, and verifies the 3+ row is the roll-up of the rows
      above it rather than an independent figure that could disagree.
- [x] The check catches a one-decimal rounding error in any cell. It found one:
      the all-valid one-vowel cell was written as 28.4% when 4,211/14,855 is
      28.3%.
- [x] `publish_poster.py --check` and the other checks still pass.
