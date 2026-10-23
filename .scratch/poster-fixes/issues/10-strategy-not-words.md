# 10: Bands carry a strategy, not a guess word

**What to build:** README calls the poster done, but its hit-count bands still
name one guess word per band. That word is only the best move for the band's
_largest_ pool: REEDY is right for 23 of the 470 two-hit games (5% of the band)
and GAWKY for 3% of the three-hit band, while the two-hit band alone recommends
125 different words across its 133 patterns. A reader takes "2 hits → REEDY" as
a rule, and if their two hits were A and L, REEDY contains neither letter.
Replace the word in each band with the band's strategy mix, which is true of
every game in it. Apply this to section II (the play-tree table) and to section
I (the method flow panel), which has the same defect.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

Section II's table becomes, verbatim, games-weighted over the 2,309 answers:

| Hits | Share | ~Left | Strategy                             | ~After |
| ---- | ----- | ----- | ------------------------------------ | ------ |
| 0    | 0.6%  | ~15.0 | Candidate — always                   | ~1.40  |
| 1    | 4.5%  | ~9.1  | Burn word — 57% of games             | ~1.31  |
| 2    | 20.4% | ~6.6  | Candidate 73% · burn 14% · split 13% | ~1.16  |
| 3    | 43.1% | ~4.4  | Candidate 72% · split 18% · burn 10% | ~1.16  |
| 4    | 26.9% | ~2.2  | Candidate — 86% of games             | ~1.02  |
| 5    | 4.5%  | ~1.0  | Candidate — always                   | ~1.00  |

- [ ] Section II names no guess word; its Strategy column shows the mix above,
      and it carries a one-line caption defining candidate, split word and burn
      word.
- [ ] Section I's flow panel also names no guess word, and its bands agree with
      section II.
- [ ] `~Left` and `~After` are games-weighted (mean pool size and mean expected
      candidates after the third guess). Aggregating `~Left` across bands
      reproduces the panel's own 4.37, which the old pattern-mean values did
      not.
- [ ] The prose claim "the hit count, not proximity, picks the next move" is
      corrected: the hit count fixes the pool size, the letters that hit decide
      between a candidate and a splitter.
- [ ] The acceptance check parses both sections and fails if any band names a
      word, or if a band's mix, share, ~Left or ~After disagrees with a
      recomputation from `data/answers.txt`.
