# 01: Measure full vowel coverage

**What to build:** `full_coverage.py`, writing `results/full_coverage.json` and
`results/full_coverage.md`. Three measurements over the 2,309 committed answers
in `data/answers.txt`.

_Full coverage_ — the branch is the exact set of A E I O U Y present, which the
feedback decides once a third coverage word has been played. For each
single-vowel branch report the answer count, its share of games, the share where
that vowel appears twice or more, the share where a consonant repeats instead,
the share where nothing repeats, and the best next guess with its expected
candidates remaining — the same sum-of-squared-feedback-groups rule
`hit_tree.py` uses, scored over `data/answers.txt`.

_Partial coverage_ — the same read with only A E I O decided (what SOARE + CLINT
gives), U and Y unknown. Reported for the same single-vowel branches so the two
reads can be compared directly.

_Cost_ — average guesses for a fixed opening of two coverage words versus three,
both continued by the same minimax policy. Reuse `simulate_method.simulate` by
overriding its `OPENERS`; do not restate the policy in a second place.

**Blocked by:** the `hit_tree.py` merge conflict. The cost measurement imports
`simulate_method`, which imports `hit_tree`; the two branch measurements run
without it. The script therefore imports `simulate_method` inside the cost
function, so the branches can be produced and checked before the conflict is
resolved.

**Status:** ready-for-agent

- [ ] `results/full_coverage.{json,md}` are written by `full_coverage.py`, and
      regenerating twice produces identical files.
- [ ] Branch rows cover all six single-vowel branches, the 12-answer Y branch
      included — omitting it would leave the "no vowel is left over" claim
      incomplete, since DUMPY is played for Y as well as U.
- [ ] Every share names its denominator: the branch's own answer count, never
      the repeat-pair or repeated-letter-instance counts `repeat_shapes.py`
      uses.
- [ ] The script reports that no answer has zero of A E I O U Y, and that
      exactly one shows in 680 of 2,309 games (29.4%).
- [ ] The expected-left values come out as A SLANT 6.27, E STEER 4.80, I SKIRT
      5.75, O STOOL 5.94, U CRUST 3.97, Y GLYPH 1.17.
- [ ] The cost block names both openings and the extra guesses per game, and its
      figures come from `simulate_method.simulate`.
- [ ] `README.md` lists `full_coverage.py` with the other one-off explorations.
