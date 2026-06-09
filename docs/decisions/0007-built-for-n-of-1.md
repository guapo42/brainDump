# ADR 0007 — Built for N=1 (personal daily use is the success criterion)

**Status:** accepted · **Date:** 2026-06-09

## Context
The builder stated the goal explicitly: the project succeeds if **they** use it
day to day and it improves their **responsiveness** (not dropping balls with
people) and **productivity** (starting/finishing real work). Helping others or
selling it is a welcome *possible side effect*, not a goal that shapes decisions
now. Without pinning this, the detailed External Lobe spec invites two classic
failure modes: building for imaginary future users, and implementing the spec's
breadth instead of the builder's daily needs.

## Decision
**Optimize every decision for one real user — the builder — and for daily use.**

1. **Success = daily use that improves the builder's work**, measured by the
   daily-driver gate (specs/05) and a weekly "did it help?" reflection, not by
   feature completeness or demo polish.
2. **No generalization for others:** no multi-user, auth, theming,
   configurability, or abstraction justified only by hypothetical other users
   (reinforces CLAUDE.md Parts II/XI). Sellability, if it ever comes, is
   downstream of being genuinely good for N=1.
3. **One of each UI surface.** Build a single capture surface, a single time
   visualization, and (if at all) a single knowledge view that earn daily use.
   The spec's variation menus are deferred unless daily use demands an
   alternative.
4. **Both halves of the goal are first-class.** Productivity/initiation (Anchor
   cockpit, P1–P3) and responsiveness/not-dropping-balls (commitments → forgetting
   → nudge). Capture *commitments* (who's waiting, when promised) locally from P2
   so responsiveness value arrives before the backend (specs/05).
5. **Cut candidates are explicit.** The force-directed knowledge graph (P6) is
   the feature least likely to survive the daily-use test; it is opt-in and must
   re-justify itself at its pre-flight.

## Consequences
- The plan's MVP cut line (P0–P3) and value-ladder framing (specs/05) are the
  operational expression of this ADR.
- When the spec and daily usefulness disagree, **daily usefulness wins** — update
  the spec, don't grind out unused breadth.
- "Would a second user want this?" is the wrong question during v1. The right one
  is "will *I* open this tomorrow?"
