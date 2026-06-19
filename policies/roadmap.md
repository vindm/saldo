# System development roadmap

> A map of the current state and directions. **Entering a new session:** this file (where we are) + `system-map.md` (how it is built) + `INSTRUCTIONS.md` (the process) + `safety-rules.md` (the boundaries).
> **Last update:** 2026-06-13.

---

## 1. Where we are now

**Clients — 16.** Team (7, in 1C:Fresh under the team accountant): Client A, Client B, Client G2, Client C, Client D, Client E, Client F (+ one more client in liquidation). Direct circuit (9, bank/e-signature held by the client): Client G, Client H, Client I, Client J (paused), Client K2, Client K, Client L, Client M, Client N.

**Source of truth — `state/*.json`** for every client (migration completed 2026-05-25; `clients_data.json` archived). Narrative — `mental_model.md` (ACTIVE: + the `analysis` block); log — `history.jsonl`; decision audit — `journal/operator_decisions.md` (audit only, not a functional source). Full map — `system-map.md`.

**Collector daemons (Scheduled, morning Bali time):** news · email · finkoper · tg-sync — self-contained (updater/analytic deprecated, logic in `mm_update`). Unconditional dashboard render at the end of each + a safety net `dashboard-render-safety-net` at 07:08. `.bak` hygiene — `bak-rotation-weekly` (Mon).

**Banks — direct pull:** T-Bank (Client N/Client G/Client H/Client I + payment provider), Alfa (Client K/Client L/Client M). Workflows `tbank/`, `alfabank/`.

**Dashboard (`engine/`):** generator `generate.py` → views Dashboard/Plan/Calendar/Periods/Clients(by group)/Guide. Guards: `state_lint` (gating), `system_integrity_check`, `snapshot`, `_waker` (waking deferred). The home view = a lens over state: Statistics → 🧠 Analysis and recommendations → Let's clarify 1-2 → Top 5 → Latest updates → Digest (brief + "needs a decision" replaced by the analysis block; fallback to the deterministic brief if there is no analysis).

**`assist` on every track** (top-level field): a system hypothesis + personalized actions (short labels, a recommended one), filled by `mm_update`, visible in the brief and in the track modal. Single track render across all views via `build_track_data_attrs` (canonical resolution by id OR source_ref). Coverage of live tracks — 100%; `state_lint:assist_gap` guards gaps.

## 2. Closed (milestones)

- **State-OS:** migration into `state/*.json`, 8-9 files per client, 22 schema extensions, lint invariants, snapshot rollback.
- **Dashboard on top of mental_model:** decomposition of `generate.py` into modules; 5 views; clickable cards → track modal; buttons → copy-modal "Prompt is ready"; dictation.
- **Workflows as infrastructure:** finkoper, email, news, tg, ofd, tbank, alfabank, egrul, websbor, mm_update.
- **Decision journal = audit** (the R5 filter of dismissed items migrated into `state/risks.json:dismissed[]`; journal parsing retired 06-07).
- **Brief + assist** (2026-06-13): the home interaction surface; assist on all live tracks; single render path.
- **"Analysis and recommendations" narrative** (2026-06-13): an end-to-end synthesis (summary + recommendations with "Dig in") replaced Brief + Needs-a-decision on the home view; system-wide + per-client; mm_update writes into `mental_model.md` (fenced `analysis`), render with a "stale" marker; lint `analysis_missing`/`analysis_stale` drives freshness (like assist_gap). Seeded for all 16 + a system-wide one on 2026-06-13.
- **R8 (aging) + tech-debt cleanup** (2026-06-13): lint `stale_track` + a "stale" badge / ranking (view-only); the dead `load_human_dismissed` removed (dismissed items — `state/risks.json:dismissed[]`).
- **Hygiene:** `.bak` rotator (weekly), garbage/orphan cleanup, the deprecation banner removed.

## 3. Open / in progress

| Initiative | Status |
|---|---|
| **1C workflow (`one_c`)** — read-only reconciliation/reading | ⏸ paused 2026-06-13. Mode — collaborative: the operator opens the form, the assistant reads it via JS (the Taxi client does not support automated clicking; see [[one_c_access_and_constraints]]). Operations: close status, KUD/KUDIR ledgers, document audit, trial balance. |
| **Deadline calendar → Calendar MCP** | 💡 idea. Deadlines from `financials.tax_calendar` → a connected calendar with reminders (on approval). |
| **Self-reflection** | 💡 analytics on the work (how many decisions/week, recurring topics). |

## 4. Session entry triggers

| Say | What I'll do |
|---|---|
| "Show status" | Open this file — where we are / what's open. |
| "New task in Finkoper" | INSTRUCTIONS Step 1.5 → the client's mental_model → `workflows/finkoper/`. |
| "Check anomalies / update" | The dashboard lens / `mm_update`. |
| "Let's continue 1C" | [[one_c_access_and_constraints]] → collaborative reading mode. |

---

_Detailed history of the P-initiatives (P0-P5) — in git/backups and `operator_decisions.md`. This file is the current state; update it when an initiative closes._
