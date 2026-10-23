# 06: Simulate the fixed-opening method

**What to build:** A measurement of the method the poster actually teaches —
play the first opener, then the second, then apply the derived guess-3 rule,
then continue until solved — over the full answer pool. It reports average
guesses, the worst case, and the share solved on each guess. Today the poster's
headline performance figure belongs to a different policy, so a reader has no
way to score the advice they are given. If the method ever needs six guesses,
that is a finding to report, not to round away.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Average guesses, worst case, and per-guess solve share for the taught
      method, over the whole answer pool.
- [ ] The simulated policy is the one the poster states; any place a stronger
      policy was substituted is named.
- [ ] Reproducible from committed inputs, with the result written as both
      markdown and json in the results directory.
- [ ] The share of games needing six guesses or failing is reported explicitly.
