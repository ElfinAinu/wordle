# 02: Section VIII - where repeats occur

**What to build:** A new poster section, appended after the existing
shape-and-mistakes section as VIII so no numeral shifts, that shows where in a
five-letter answer a repeated letter actually sits. The centrepiece is a
slot-pair grid: a 5x5 upper triangle, one cell per pair of slots, each shaded by
that pair's share of repeat pairs, reusing the letter grid's existing cell
styling so the poster keeps one visual language. Touching pairs must be
distinguishable at a glance from separated ones, because most repeats do not
touch. A caption line carries the split that the grid cannot show: 43% of
repeats touch and 57% are separated, touching repeats are consonant-heavy while
separated ones are vowel-heavy, and 81% of repeats involve a letter the opening
tests - so the reader sees one copy and cannot tell there are two - against 19%
that involve a letter it never tests, where nothing shows.

**Blocked by:** 01 (Measure how repeats are shaped)

**Status:** ready-for-agent

- [ ] The section exists as VIII, appended, with no existing numeral or section
      renumbered.
- [ ] The grid is a 5x5 upper triangle, one cell per slot pair, shaded by share
      of repeat pairs, reusing the existing cell styling; the raw count is
      available on hover.
- [ ] Touching pairs read as different from separated pairs at a glance.
- [ ] The caption states the touching/separated split, the class skew and the
      visibility split, and the section says what its denominator is (repeat
      pairs for the grid, repeated-letter instances for the splits).
- [ ] An acceptance check re-derives every figure the section prints from
      `data/answers.txt` and fails when any drifts.
- [ ] `publish_poster.py --check` still passes, and the band guard is
      unaffected.
