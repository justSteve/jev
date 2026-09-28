# jevdesk — design spec (first draft)

- **Date:** 2026-09-28 · **Bead:** `dr-nbv` (DReader beads) · **Restore point:** tag `jevdesk-design-cp1` (`docs/design/2026-09-28-jevdesk-design-checkpoint-1.md`)
- **Status:** approved in brainstorming, section by section; awaiting Steve's review of this written spec before the implementation plan.

## 1. Purpose

A decision-support agent for discretionary intraday futures trading, built on the
general form of Christopher Creamer's "Auction Resolution" (AR) framework. It
reduces a messy decision tree to one of four verdicts per checkpoint, using
Jev (TypeSafe's decision model) for the fuzzy judgments and code for everything
else.

It is a **first draft of the general form**, not a finished trading system.
Steve's understanding of the source framework has gaps, and Steve will not
adopt all of its absolutes. So every absolute is a profile setting, and the
framework's known internal conflicts are profile switches.

**Not in scope:** order execution or any broker connection; live market-data
feeds; automated trading. The agent advises, and Steve acts.

## 2. Principles

1. **Jev never decides the trade.** It answers single, typed judgments
   (`noul` = probability of yes, `choice`, `score`). Code does all
   arithmetic, applies every gate, and composes the verdict.
2. **An entered fact beats a judgment.** If Steve supplies a number (delta
   values, imbalance cells, a print size), code evaluates it and Jev is not
   asked. Jev fills only the gaps where Steve has a description.
3. **Every Jev answer has one job.** Each judged question feeds exactly one
   gate, so every verdict can name the answer that caused it.
4. **Uncertain means not yet.** A judgment below its confidence threshold
   produces NEED-INFO, never a guess.
5. **The general form is public; his specifics are private.** This repo is
   public. Profiles and scenarios carrying Creamer's values (drawn from his
   gated PDFs and from verified frames) live outside it (§ 7).

## 3. Interaction

Steve works in a **local web page** served by a small Python server in this
repo, like jev-loop's dashboard. The engine and the Jev key stay server-side;
the key is never in the page. There is one form per checkpoint. Steve enters
facts and short plain-language descriptions and submits; the page shows the
verdict, the gate that decided it, the reasons, and (for NEED-INFO) what to add.

## 4. Checkpoints

The checkpoint and gate names below are the general form. The profile supplies
all values.

| # | Checkpoint | Steve enters | Code computes | Jev judges (one call per checkpoint) |
|---|---|---|---|---|
| 1 | **Pre-market map** | HTF swing highs and lows (per the profile's bias timeframes); gamma levels (HVL, call wall, put wall, transition levels); session highs and lows; a short description of structure and the overnight | fib levels and the entry zone (execution and awareness timeframes per the profile); **gamma regime from price vs HVL and the transition levels**; distances to levels | `bias` (choice: bullish / bearish / unclear); `environment` (choice: balance / imbalance / compression); `session_path` (choice among the profile's scenarios) |
| 2 | **At location** | current price; which marked level price is at | inside the zone or not; whether the level type is allowed by the profile; cutoff-time check | `meaningful_location` (noul), only for level types the profile marks "judged" |
| 3 | **Confirmation and entry** | a description of the tape at the level; optional hard facts (delta values, imbalance cells, print sizes); proposed entry and stop; instrument | imbalance ratios and stack count (if cells are given); delta flip (if values are given); stop distance vs cap; position size from the risk budget and point value; volatility size cut | reversal: `aggression_failed` (noul), `pressure_flipped` (noul), `absorption_or_exhaustion` (choice); continuation: `acceptance_confirmed` (noul) |
| 4 | **In trade** | entry, stop, current price; a description of what just happened | open R; breakeven-by-points (only if the profile allows it) | `management_event` (choice: structure break / dominance print / passed prior counterparty supply / accepted aggression / failed counter-aggression / none); `absorbed_again` (noul) |
| 5 | **Session** | trades and P&L so far, the time, a short self-report | loss count vs limit, P&L vs limit, time vs cutoff | `tilt_level` (score: none … stop) |

The regime is computed, not judged: the source's written rule maps price
relative to the HVL and the transition levels to a regime.

## 5. Verdict composition

- Gates run in the profile's order, which follows the framework's layers:
  environment → location → path → confirmation → risk. The first gate that
  settles the question stops the walk.
- **Each gate returns one of four outcomes:**
  - *pass-through:* the condition is met; go to the next gate.
  - *PASS:* a hard condition failed; the trade is off, with the reason named.
  - *WAIT:* the condition is not met yet but could be.
  - *NEED-INFO:* a judged gate is below its confidence threshold, or a
    required input is missing. The verdict states what to add.
- The profile sets, per gate, whether a failure means **PASS or WAIT**.
- **ACT** only when every gate passes through. It returns the computed plan:
  entry, stop, size, and the target ladder from the profile's order.
- **Thresholds:** a `noul` gate passes when its probability clears the gate's
  threshold. A `choice` or `score` answer counts only when its confidence
  clears the gate's minimum; otherwise the gate is NEED-INFO. The profile's
  defaults start at 0.60 and are adjusted from the log.
- **Advisory gates (the discretion switch):** a profile may mark a judged gate
  `advisory`. Its failure is reported but does not block; the verdict becomes
  `ACT (advisory gate failed: <gate>)`. This lets a profile express either "no
  discretionary override" or "trade the tape".

## 6. Failure handling

| Failure | Behaviour |
|---|---|
| Jev unreachable or timed out | NEED-INFO ("judgment unavailable"), listing the gates that could not be evaluated. Never a default answer. |
| Malformed Jev response | Validated like jev-loop's `validate_answers`; treated as unavailable. |
| Mock client in use | Only when chosen explicitly (`--mock`); labelled on every verdict and log line. |
| Bad input (stop on the wrong side, a required field missing, a price outside the entered range) | Rejected on the form before anything runs. |
| Profile error (unknown gate, threshold out of [0, 1], missing required value) | The server refuses to start and names the fault. |

## 7. Profiles, scenarios and privacy

- **Profile** (TOML, read with the stdlib `tomllib`): gate order; per-gate
  failure mode (PASS/WAIT), threshold and advisory flag; the allowed level
  types and which are judged; zone bounds; bias and execution timeframes;
  stop cap; risk per trade and account size; point value per instrument;
  volatility size-cut rule; session cutoff; loss limits; the breakeven mode
  (event-driven, or by points with N); target ladder; the session-path
  scenario names; and switches for each of the framework's known conflicts
  (for example, whether the delta flip is mandatory for reversals, and whether
  discretion may override).
- **In this public repo:** `jevdesk/profiles/template.toml` with placeholder
  values and comments naming each setting's role. There are no values from
  the source framework.
- **Private, outside the repo:** `~/.jevdesk/profiles/creamer-written.toml`
  (his rulebook as written) and Steve's own profile, copied from it and
  edited; `~/.jevdesk/scenarios/*.toml` (the worked-example fixtures);
  `~/.jevdesk/log.jsonl`. The path can be changed with `JEVDESK_HOME`.
- Conflicts and their sources are catalogued in the private DReader synthesis
  (`media-reader/playlists/creamer-decision-system.md`, "Conflicts for Steve
  to rule on"). The profile references that list; it does not restate it.

## 8. Components

A new package `jevdesk/` beside `jevloop/`, reusing jevloop's decision client
(`client.py`: TypeSafe direct → Vercel AI Gateway → mock), its vault loading
(`vault.py`) and its arithmetic guard (`split.py`'s marker check).

| Module | Job | Depends on |
|---|---|---|
| `jevdesk/profile.py` | Load and validate a TOML profile into typed settings; refuse faults. | stdlib |
| `jevdesk/model.py` | Dataclasses: checkpoint inputs, gate results, verdicts, plan. | — |
| `jevdesk/compute.py` | Pure functions: fib levels and zone membership, regime from levels, imbalance ratio and stack count, delta flip from values, stop distance, size, volatility cut, time and loss checks, open R. | model |
| `jevdesk/questions.py` | Build each checkpoint's judged questions from the profile, skipping any gate that an entered fact already settles; run every question through the arithmetic guard. | jevloop.split |
| `jevdesk/judge.py` | Send one checkpoint's questions in one call via jevloop's client; validate answers; map failures to "unavailable". | jevloop.client, questions |
| `jevdesk/engine.py` | Walk the profile's gates for a checkpoint; combine computed and judged results into a verdict and plan. | profile, compute, judge, model |
| `jevdesk/log.py` | Append one JSON line per evaluation; record an outcome against a logged evaluation later. | — |
| `jevdesk/server.py` | Local HTTP server (stdlib): serve the page, accept a checkpoint submission, return the verdict as JSON. | engine |
| `jevdesk/web/index.html` | Five checkpoint forms and the verdict display; no external assets. | — |
| `jevdesk/__main__.py` | CLI: `serve`, `eval --checkpoint N --input FILE`, `check-profile PATH`, `init-profile` (copy the template into `JEVDESK_HOME`). | all |

**Packaging:** add `jevdesk` to the setuptools package list, and raise
`requires-python` to `>=3.11` for `tomllib` (the venv runs 3.12). No new
dependencies.

## 9. Logging and calibration

One line per evaluation: timestamp, profile name, checkpoint, inputs, the
questions sent, Jev's raw answers with the model that answered, each gate's
outcome, the verdict, and whether the mock was used. `record-outcome` attaches
what happened afterwards. A later calibration step (like jev-loop's Brier and
reliability report) can then test whether each judged gate's probabilities
hold up and adjust its thresholds. The calibration report itself is **out of
scope** for the first draft; only the log format must support it.

## 10. Testing

1. **Unit tests (pytest):** every computed function; the verdict composer
   (ordering, PASS vs WAIT, NEED-INFO on low confidence, the advisory switch,
   fact-beats-judgment skipping); the profile loader's refusals; every
   generated question passes the arithmetic guard. The tests use invented
   values only.
2. **Scenario tests:** worked examples from the source material, stored in
   the private scenarios folder, with **scripted** Jev answers. Each asserts
   the verdict the `creamer-written` profile should give, including cases that
   should come out PASS under his written rules even though he traded them.
   A pytest marker skips these when the private folder is absent, so the
   public suite always runs.
3. **Live smoke run (manual):** a few scenarios against real Jev, if a key is
   in the vault. This checks the judgments are sensible and confident
   enough. It is not in the automated suite.

## 11. Open items (not blocking the plan)

- Whether a live Jev key is in the vault (`/home/vault/jev/env`). The draft
  runs on the labelled mock without one.
- Writing `creamer-written.toml` means turning the synthesis into settings.
  Where the source conflicts, that profile follows his *written* rules (his Resolution Model
  Framework and Trade Management documents) and records each conflict's
  alternatives as comments. Steve's own profile is where rulings are made.
