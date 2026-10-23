# 11: Pattern cards state their selection, not a band strategy

**What to build:** The guess-3 pattern cards currently title themselves with a
strategy — "1 hit — Burn word", "2 hits — Candidate, Split word" — and those
titles list the actions of the three rows _displayed_ on that card, not the
actions across the band. On the same page section II now states the band's real
mix, so the two disagree for three of the six bands: 1 hit is burn 57% /
candidate 35% / split 8%, 2 hits is candidate 73% / burn 14% / split 13%, 4 hits
is candidate 86% / split 11% / burn 3%. A reader also cannot tell that the rows
are examples at all: each card shows the three largest pools out of its band's
19, 133 or 426 patterns. Title the cards by hit count alone and let the existing
ACTION column carry each row's label — it already does, and it is right — and
state on every card that the rows are the band's largest pools. The rows
themselves need no change: all twelve words, candidate counts and `Left` values
reconcile with an independent recomputation.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] No card title names an action; titles are the hit count only.
- [x] Every card states that it shows the band's largest pools, with how many it
      shows and how many the band has.
- [x] Each row's ACTION label still matches that row's pattern, and every word,
      candidate count and `Left` still reconciles with a recomputation from the
      answer list.
- [x] The acceptance check no longer requires an action name in a card title,
      and fails if one returns; every check in the suite still passes.
- [x] Deployment happens once for the whole spec, not from this ticket.
