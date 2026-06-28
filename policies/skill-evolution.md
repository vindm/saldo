# Self-improving skills — the learning loop (mechanics evolve, safety doesn't)

Saldo's skills are the program the AI runtime executes. The runtime is also its own
**programmer — but bounded**: UI/mechanics knowledge improves by doing; protocol and safety never
change by learning. This file is the contract for that.

## Two layers, only one evolves

- **Protocol & safety** — shared (`connectors/_chat_actions.md`, `_chat_collector.md`,
  `_sources.md`, `mm_update/SKILL.md §D`, `policies/safety-rules.md`): the **WHAT** + the gates.
  **Immutable by the learning loop.** A learned step may NEVER weaken or skip an approval gate,
  a recipient/account verification, the close model, or a credential rule. If a lesson implies
  changing safety → STOP; that is an operator decision, not a learned amendment.
- **UI playbook & mechanics** — per provider (`connectors/<x>/ui_playbook.md`): the **HOW** for
  that web app. **Learnable.**

## The loop (per action)

1. **Execute** per the playbook's canonical steps.
2. **Verify the outcome objectively** — message actually sent (a sent-tick / message id), file
   found, right account (whoami). You can only learn from a mistake you can **detect**; never
   trust the AI's belief of success.
3. **On deviation** (a step fails, a selector is gone, no instruction exists): **recover** —
   observe the live page (`get_page_text`/screenshot), accomplish the goal by reasoning over the
   DOM — then **capture** what actually worked. Never silently repeat a failing step, **and never
   mask it by degrading to a weaker signal/method** (an external read-indicator instead of our
   watermark, or scanning the rendered DOM instead of the intended set) — recover toward the goal
   via a *more reliable* route, then capture (`connectors/_ui_playbook.md` → "Recover toward the
   goal").
4. **Capture (auto, tentative)** — append a dated **Field note** to the data-dir overlay
   `<data.dir>/journal/playbook_notes/<provider>.md` (what changed, the working step, the
   evidence) — **never** the engine playbook. This records; it does not change canonical behavior,
   so the runtime writes it without approval.
5. **Promote (gated)** — a Field note becomes a **canonical step** only when: (a) **corroborated**
   (worked ≥2× or operator-confirmed), (b) it touches **no safety**, (c) **operator-approved**
   (or auto with a confidence threshold + one-tap rollback). Promotion is a behavioural change →
   bump the playbook version + add/adjust a scenario (`CLAUDE.md` Invariant-0).

> **Capture is free; promotion is gated.** Recording what happened is safe and autonomous;
> changing the program is reviewed.

## Safeguards (the failure modes)

- **Overfit to a glitch** → tentative until reproduced; a single transient failure rewrites nothing.
- **Hallucinated lesson** → promotion is operator-gated; verification must be objective, not self-asserted.
- **Drift / bloat** → notes are dated + provenanced; a periodic **consolidation** pass supersedes
  stale notes and GCs selectors that the UI has changed (like memory consolidation).
- **Safety regression** → the safety layer is immutable by the loop (above).
- **Boundary** → playbooks describe the **web app**, never a client's data or credentials
  (public/clean; secrets in `secrets/`). A Field note contains **zero real client data**.

## Inputs

- **Self-discovery** during execution (the loop above).
- **Operator teaching** — including teach mode (`request_teach_access`/`teach_step`): the operator
  demonstrates the procedure on screen; the runtime records the steps into the playbook.

## Where it's stored — canonical in the engine, learned in the data dir

🔴 The running instance must **never modify engine code** — it's pulled clean from upstream;
editing it breaks `git pull` updates and violates Boundary #1 (clean public engine, zero real
data). So the two layers live in two places:

- **Canonical steps** — `connectors/<x>/ui_playbook.md` in the **engine** (version-controlled,
  **read-only at runtime**). Improved **upstream by the developer** and shipped to every operator
  via an engine pull.
- **Learned Field notes** — `<data.dir>/journal/playbook_notes/<provider>.md` in the operator's
  **data dir** (per-instance, **runtime-writable**, NOT in git — travels with the data like
  `journal/`, `state/`, the data-dir `instance.yaml`). This is the **only** place the running
  instance writes what it learns. Zero real client data (it describes the web app, not a client).

At execution the runtime **composes** canonical + the instance's overlay (the overlay wins for a
primitive it has corrected). Not in assistant memory — procedural product knowledge lives in the
product's own data.

## Two-tier promotion

1. **Instance-local** — in the data-dir overlay, a Field note goes `tentative → corroborated`
   (worked ≥2× or operator-confirmed). Helps **this** operator immediately; **no engine change**.
2. **Upstream** — a corroborated, broadly-true lesson is **curated by the developer** from
   operator overlays into the engine canonical playbook (review + scenario + version bump) and
   shipped to all via pull. The running instance **never** promotes into engine code itself.

## Related

- `connectors/_ui_playbook.md` — the per-provider playbook structure.
- `connectors/_chat_actions.md` / `_chat_collector.md` / `_sources.md` — the immutable protocol layer.
- `policies/safety-rules.md` — the gates the loop may never touch.
