# 02: Section IX - full vowel coverage

**What to build:** A ninth section on the poster, `id="vowels"`, after section
VIII.

It is **conditional**, and the framing is the point. Sections III and IV assume
the reader stops after SOARE and CLINT. This section is the alternative for a
reader who spends guess 3 on a coverage word — DUMPY, the word those tables
already recommend when both openers come back gray. Section I does not move:
still two openers, still ten letters tested. The section says so by
cross-referencing III and IV rather than presenting itself as the new method.

Content, in the poster's existing idioms:

- **Six bars**, one per vowel A E I O U Y, reusing the `dist-bar` / `dist-col`
  furniture section V already uses for its distribution, with the E bar carrying
  `class="opt"` the way section V marks its mode. Each bar is the share of that
  branch where the vowel appears twice or more, scaled to the tallest (E,
  69.3%); each card also carries the branch's share of games, the next guess and
  its expected candidates remaining.
- **A rule card** — only E or O shows means the vowel doubles (STEER, STOOL);
  only A, I, U or Y shows means five distinct letters (SLANT, SKIRT, CRUST,
  GLYPH).
- **A cost card** — a third coverage word costs 0.58 guesses a game, 3.61 to
  4.20, so spend it when the two openers leave the vowel set vague. What it buys
  is a branch of roughly half the size: the same only-E read is 301 games on
  TERSE at 7.66 without U and Y decided, and 166 games on STEER at 4.80 with
  them.

**Blocked by:** 01

**Status:** done

- [x] Section IX appears after VIII, `id="vowels"`, titled "Full vowel
      coverage", with a `sec-meta` that says it is conditional.
- [x] The section cross-references sections III and IV, and section I still
      states two openers and ten letters tested.
- [x] The chart has six cards, each with the branch's share of games, the repeat
      share the bar encodes, the next guess and its expected left.
- [x] The rule the section teaches is re-derived by the check, not grepped: for
      E and O the best next guess must repeat a letter, and for A, I, U and Y it
      must not.
- [x] The section states that no answer has zero of A E I O U Y, and that
      exactly one shows in 29.4% of games.
- [x] Every denominator is named as a branch size, and the section says so
      explicitly so it is not confused with section VIII's 786 repeated-letter
      instances or 826 repeat pairs.
- [x] `publish_poster.py --check` passes.
- [x] The repeats-section check that pins the poster's section numerals is
      extended to IX; nothing is renumbered.
- [x] `results/full_coverage.json` exists, so the check can verify the cost
      figures.

## Resolved

The section states the coverage cost (3.61 / 4.20 / 0.58). While the
`hit_tree.py` conflict was open, `results/full_coverage.json` could not be
generated and the acceptance check failed on that one point and nothing else —
deliberately, so the poster could not ship a figure with no committed source.
Ticket 01 has since run: the file exists, the cost measured 3.6146 -> 4.1953,
matching the throwaway harness that had reproduced the committed two-opener
average exactly. The check passes.
