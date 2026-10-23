# 12: Make the shared feedback function correct when the guess repeats a letter

**What to build:** The shared pattern function marks a tile yellow when the
guess carries a duplicated letter and the answer carries fewer copies, because
it compares the answer's letter count against greens only and ignores yellows it
has already assigned. Against a hand-written reference it is wrong on 612 of
2,309 answers for the guess `reedy`, 454 for `eerie` and 446 for `aback`, and
correct for every guess with five distinct letters — which is why the poster
itself is unaffected. Make the shared function return what the game returns, pin
it with a regression check, and delete the private copies that two other modules
grew to work around it so the fix cannot drift apart again. Do not regenerate
any result output here; that is the next ticket.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] The shared function agrees with the game's rules for duplicated guess
      letters, duplicated answer letters, greens that consume an answer's
      letter, and letters absent from the guess.
- [x] A regression check covers every answer for repeated-letter guesses plus
      hand-written edge cases, and fails against the previous implementation.
- [x] No module keeps a private feedback implementation; the shared one is the
      only one.
- [x] Every published figure on the poster is unchanged: the distinct-letter and
      tiles-lit coverage rates, the candidates-left headline, the per-band
      mixes, and the simulation's average and worst case.
- [x] The full check suite passes.
