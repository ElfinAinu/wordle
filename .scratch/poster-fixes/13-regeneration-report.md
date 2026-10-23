# Ticket 13 — regeneration report

**Commit:** `f08c1a3`
(`fix(results): regenerate stale feedback-dependent outputs`) **Baseline diffed
against:** `main` (`748c5fc`); ticket 12 and 11 did not touch `results/`, so the
pre-regeneration tree is the same as `f08c1a3^`. **Scope:** seven regenerated
output files. No script, poster, check or deploy file changed.

Ticket 12 corrected the shared feedback function (`analyze.pattern_codes`);
before that fix it marked extra yellows for guesses that repeat a letter. Every
result whose search ranged over a repeated-letter guess was therefore computed
against wrong feedback. This report records the resulting movement per file,
reconstructed from `git show f08c1a3` and the implementer's run.

## Per-file movement

| File                                   | Moved                                                                                                                                                                                                               | Unchanged                                                                                                        | Why                                                                                                                                                                                                                                                                                                                    |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `results/analysis.{json,md}`           | Notable opener ranks: LOUIE 725→730, ADIEU 3396→3446, AUDIO 6107→6237. Their entropy and expected-remaining are identical.                                                                                          | Letter statistics and the whole top-25 opener table.                                                             | `rank_openers` iterates the full 14,855-word pool. The three notables have five distinct letters, so their own scores do not change, but corrected scores for repeated-letter guesses reorder the ordinal ranks around them.                                                                                           |
| `results/pairs.{json,md}`              | ROATE headline 3.14→3.12, RAILE 3.19→3.18, SOARE 3.29→3.27, RAISE 3.37→3.35. ROATE tree: LENES ~3.88→3.69, FEUED ~7.04→6.94 (same words); YXYXX pick MIRAH ~2.43 → CARRS ~2.37; XXGYG pick GLISK ~1.0 → GLEEK ~1.0. | SLATE 3.14, TARSE 3.15, TIARE 3.21, REAST 3.29; every `solved_on_two_pct`; the TWEEL/ATTAR/AAHED picks.          | The optimal-second-guess search ranges over all guesses. LENES (repeats E) and FEUED (repeats E) score lower under correct feedback; CARRS (repeats R) and GLEEK (repeats E) now beat the distinct-letter MIRAH/GLISK. Lower per-pattern values pull the headline down.                                                |
| `results/exhaustive_all.md`            | Scored pairs 361661→361389 (−272); pairs beating baseline 4741→4708 (−33).                                                                                                                                          | Baseline SOARE+CLINT (remaining 30.724, solved-on-2 6.99%, spot 65.4%); the top-20 table; `exhaustive_all.json`. | The first-guess pool is the `rank_openers` top-300 over the all-words universe. Correcting feedback swaps exactly one word there: TIROS leaves and SAREE (repeats E) enters at rank 249. Different first guesses contribute different disjoint-second counts, which shifts the totals; no individual pair row changed. |
| `results/vowel_tree.{json,md}`         | AE: TERSE 19.4→18.85; E: RESET 9.37 → TERSE 7.66; IO: SNORT 4.6 → TORSO 4.57.                                                                                                                                       | The other 12 branches.                                                                                           | Guess 3 is the minimum expected-remaining word over the answer pool. TERSE (repeats E) and TORSO (repeats O) score lower under correct feedback, enough to change those picks and their reported `Left`.                                                                                                               |
| `results/exhaustive_answers.{json,md}` | —                                                                                                                                                                                                                   | Unchanged.                                                                                                       | Its first-guess pool is ranked over the 2,309-answer universe and the surviving set and top rows are identical — evidence the bug did not move this scan.                                                                                                                                                              |
| `results/coverage.{json,md}`           | —                                                                                                                                                                                                                   | Unchanged.                                                                                                       | Reported top pairs are distinct-letter; repeated-letter second guesses never reach the top 200, so the SOARE+CLINT rates are untouched.                                                                                                                                                                                |
| `results/hit_tree.{json,md}`           | —                                                                                                                                                                                                                   | Unchanged.                                                                                                       | Re-confirmed against the shared function (the ticket 12 prediction).                                                                                                                                                                                                                                                   |
| `results/simulate_method.{json,md}`    | —                                                                                                                                                                                                                   | Unchanged (average 3.61, worst 6).                                                                               | Re-confirmed.                                                                                                                                                                                                                                                                                                          |
| `after_gray.py` stdout                 | —                                                                                                                                                                                                                   | Byte-identical.                                                                                                  | The 15-candidate pool and positional frequencies are feedback-free; the top-10 entropy ranking is all distinct-letter guesses.                                                                                                                                                                                         |
| `compare.py` stdout                    | —                                                                                                                                                                                                                   | Byte-identical.                                                                                                  | All four compared pairs have distinct letters.                                                                                                                                                                                                                                                                         |
| `duplicates.*`, `shapes.md`            | —                                                                                                                                                                                                                   | Unchanged.                                                                                                       | No feedback dependency.                                                                                                                                                                                                                                                                                                |

## Published figures, before → after

Nothing the poster publishes moved; no poster correction was needed.

| Figure                             | Source                          | Before            | After             |
| ---------------------------------- | ------------------------------- | ----------------- | ----------------- |
| Distinct-letter share              | `coverage` / check 04           | 65.4%             | 65.4%             |
| Tiles-lit share                    | `coverage` / check 04           | 60.9%             | 60.9%             |
| Candidates left after two          | `exhaustive_answers` baseline   | 4.367             | 4.367             |
| Pinned before guess 3              | `exhaustive_answers` / check 01 | 27.76%            | 27.76%            |
| Hit-band mixes, `~Left` / `~After` | `hit_tree`                      | unchanged         | unchanged         |
| Simulation average / worst         | `simulate_method`               | 3.61 / 6          | 3.61 / 6          |
| Ladder rungs                       | check 07                        | 3.42 / 3.61 / 3.8 | 3.42 / 3.61 / 3.8 |

## Verification

- Determinism: all 10 affected scripts were run twice (`analyze`, `pairs`,
  `coverage`, `exhaustive answers`, `exhaustive all`, `vowel_tree`,
  `after_gray`, `compare`, `hit_tree`, `simulate_method`).
  `sha256sum results/*.json results/*.md` was identical between the two runs,
  and `after_gray`/`compare` stdout was identical.
- Checks: `checks/01`…`07` each `PASS`; `check_guess3.py` passed all acceptance
  criteria; `tests/test_pattern_codes.py` passed.

## Notes

- The `3.14` string in `infographic-v4.html` is a hit-tree per-pattern `~Left`
  value (unchanged), not the pair-tree headline.
- Deploy (`publish_poster.py`) was out of scope for this ticket; no served
  branch was touched.
