# jevdesk — design checkpoint 1 (2026-09-28)

A restore point in the design conversation for a Jev-based decision-support
agent built on Christopher Creamer's "Auction Resolution" (AR) trading
framework. To resume from here, a new session reads this file and continues
at **"Next step"** below. Git tag: `jevdesk-design-cp1`.

Tracking bead: `dr-nbv` (DReader beads). Brainstorming stage: structure
approved; questions, verdict logic and testing not yet presented.

## Goal (Steve's words, 2026-09-28)

> There are gaps in our understanding of Creamer's trading system that we
> can't account for — there are absolutes in his system that I'm not going to
> transfer to my own. Therefore, we are not in a position to create a Jev
> instance [in] final form. … Instead, we want to start with the general form
> of Creamer's system and create a generalized Jev agent that can support it.
> Jev takes messy decision trees and reduces them to action. … a first draft of
> a Jev-based decision support to Creamer's system as captured (incompletely).

**Source material (private):** DReader `media-reader/playlists/creamer-decision-system.md`
(the synthesis of 13 videos, a 4h25m course and 4 framework PDFs: 14 decisions,
graded written/said/shown/done, with 13 conflicts for Steve to rule on) and
the per-source cards in DReader `media-reader/dossiers/`. The DReader repo is
private; this repo is public, so none of Creamer's gated material or specific
values are reproduced here.

## Decisions taken

| # | Question | Answer |
|---|---|---|
| 1 | Where does the market view come from? | **Steve's observations.** At each checkpoint Steve (or Claude) supplies facts: levels, prices, and a short description of the tape. Code computes the numbers, Jev judges the descriptions. No data feed in the first draft. The worked examples from the source material become test cases. |
| 2 | How does Steve interact with it? | **A web page**, served locally: a small Python server in this repo, like jev-loop's dashboard, keeps the engine and the Jev key server-side, with the form in the browser. The Jev key cannot sit in a published page. |
| 3 | Where does the code live? | **In this repo (justSteve/jev)**, as a new package beside `jevloop/` (working name `jevdesk/`), reusing jevloop's decision client, mock client, vault loading and question guard (`split.py`). DReader only supplies the source material. |
| 4 | Approach | **A: the tree as data, the engine generic** (chosen over B, a hard-coded tree like jev-loop's policy.py, and C, a single composite setup score, which would lose the binary gates). |

## Approved structure (section 1)

- **Principle.** Jev never decides the trade. It answers the fuzzy judgments
  inside the decision tree ("balance or imbalance?", "did aggression fail at
  the level?", "is the tape accepting or rejecting?"). Code does all
  arithmetic, applies all gates, and composes the verdict. Nothing is sent to
  any broker: decision support only.
- **Checkpoints**, following the synthesis:
  1. pre-market map: bias, gamma regime, session path, zones, scenarios;
  2. at location: environment gate, qualifying location;
  3. confirmation and entry: reversal or continuation model, entry, stop;
  4. in trade: breakeven, trail and exit events;
  5. session: stop-for-the-day.
- **Gates** are either *computed* (code, from numbers Steve enters) or
  *judged* (a typed Jev question, from Steve's description): `noul`
  (probability of yes), `choice`, `score`. Judged questions must be single
  judgments, never arithmetic; jevloop's `split.py` guard is reused to enforce
  this. Each checkpoint's judged questions go to Jev in **one call** (jev-loop's
  speculative fan-out); code then uses the relevant answers.
- **Confidence gating.** An answer below the profile's confidence threshold
  makes the result "not yet" / NEED-INFO rather than a guess.
- **Profiles** hold every absolute: zone bounds, stop cap, risk per trade,
  session cutoff, loss count, whether the delta flip is mandatory, whether
  discretion may override, confidence thresholds. A `creamer-written` profile
  encodes his rulebook; Steve copies it to his own. Creamer's 13 conflicts
  become profile switches.
- **Verdicts:** ACT / WAIT / PASS / NEED-INFO, each with the gate that decided
  it, and what is missing when NEED-INFO.
- **Logging:** every run (inputs, Jev answers, verdict) is logged for later
  calibration (whether Jev's confidence is trustworthy), as jev-loop does.
- **Web page:** one form per checkpoint; the verdict with its reasons.

## Open items

- **Where the `creamer-written` profile's values live.** This repo is public
  and his values come from gated PDFs. Options: keep profiles outside the repo
  (a path in the vault or a private location), keep that profile in DReader
  (private), or make this repo private. To decide before the profile is
  written.
- Whether a live Jev key (TypeSafe direct or Vercel AI Gateway) is in the
  vault. jevloop's mock client lets the draft run without one.

## Next step

Continue brainstorming at **design section 2**: the concrete checkpoint
schemas (what Steve enters at each checkpoint), the Jev question list per
checkpoint (type, instructions, criteria), the verdict-composition logic and
confidence gating, error handling (Jev unavailable, schema mismatch), and
testing (worked examples from the source material as fixtures; mock client).
Then: spec in this repo, Steve reviews, writing-plans, implementation.
