# 14: Deploys get one source of truth

**What to build:** The served branch carries its own copy of the poster beside
the file it actually serves, so a deploy can copy a stale poster over a stale
poster and look like success — which is exactly what happened on the last
deploy. Give the deploy one source: the served artefact is copied from the
default branch under guards that abort on any retracted claim, on a guess word
reappearing inside a hit band, or on the served and source files differing after
the copy. Remove the duplicate poster copy from the served branch so the trap
cannot recur, and leave the source of every served file unambiguous.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] A single documented step produces the served page from the default branch
      and refuses to publish when a guard fails.
- [x] The guards cover the retracted claims, guess words inside hit-count bands,
      and a source/served mismatch.
- [ ] The served branch no longer carries a duplicate copy of the poster beside
      the file it serves.
- [x] Running the step twice in a row is a no-op the second time.
- [ ] The served page still loads, and the live URL is re-verified after the
      change.

_Pending publication: the duplicate-copy removal and the live-URL re-verification complete when this spec is published._
