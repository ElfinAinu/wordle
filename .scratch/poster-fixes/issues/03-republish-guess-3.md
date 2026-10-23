# 03: Republish the guess-3 section from the derived rule

**What to build:** The poster's guess-3 reference and per-pattern tables rebuilt
from the ticket-02 output, so the section reads as one coherent procedure: the
hit-count table and the pattern tables agree with each other, every action label
matches its word, and the prose above them describes the rule actually shown.
The section should be verifiable by eye — a reader tracing any displayed row
should reach the printed word and the printed candidate count.

**Blocked by:** 02 (derive a logically sound guess-3 rule)

**Status:** ready-for-agent

- [x] Every row in the rebuilt section comes from the derived rule's output,
      with no word or count transcribed by hand.
- [x] The section's prose states the rule the tables follow.
- [x] Recomputing the tables from committed inputs reproduces every displayed
      candidate count and candidates-left-after figure.
- [x] The section's tier names no longer promise an action the shown word does
      not perform.
