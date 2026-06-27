# Skill: question_resolver — residue auto-resolution of open questions

**The named `open_question` rung logic** (the same runtime) — the acquire-and-close procedure for
open questions: walk every open question **still open**, try to **answer it from a source the
system can reach itself**, and — when the answer is confident and objective — apply the fact and
close the question, so the operator's queue holds only what genuinely needs a person.

> **Not a separately scheduled daemon.** `resolution_sweep` (the one scheduled actualization
> daemon, 07:00) runs this logic over open questions as part of its pass over all active tasks —
> there is no separate `question_resolver` cron job. This file stays as the reusable contract
> that `resolution_sweep`, `mm_update`, `documents`, and `egrul` point at.

> **Not a revival of the deprecated `updater`/`analytic` daemons.** Those were rule-based
> patch *proposers* that applied almost nothing. This is a cognitive agent that runs the
> **mm_update** protocol (`connectors/mm_update/SKILL.md`) — it reads, decides, and writes
> state directly. "The daemon is the same me, just launched on a schedule."

## Why this exists

Most open questions are **acquisition, not decisions** — the answer already sits in a file in
Drive, a registry reachable by a known key (EGRIP by INN), 1C, the OFD, or a bank statement.
Surfacing those to the operator as "Скачать… / Найти… / Извлечь…" cards (worse, as a
copy-paste prompt) is the **fake-autonomy** failure described in `mm_update/SKILL.md
§ Derive before asking`. This skill does that acquisition work so the morning queue contains
only what genuinely needs a person.

## Trigger & ordering — runs within the sweep, AFTER the collectors (the residue rule)

- Invoked by `resolution_sweep` (`07:00`, after the morning collectors at 06:00–06:30, before the
  monitors/`dashboards`) — no separate schedule entry of its own.
- **Why after, not before:** the collectors (news/email/tg/whatsapp/max/**documents**) apply
  fresh data inline and **close the questions that new data answers** — a synced statement
  settles the bank question, an ingested document closes a "needs a document" question. Running
  the resolver *after* them means it works **only the residue still open** — it never re-does a
  collector's job and never re-checks an already-solved question. (Running it before the
  collectors, as in the old `03:00` slot, did exactly that double work.)
- **A `no_auto_resolve` question is a re-evaluatable hint, not a permanent skip.** Normally pass it
  over (the answer was external/narrative). But re-check each run whether it became objectively
  resolvable (its hypothesis/`next_action` now names a state check, e.g. «счёт в `accounts.json`»):
  if so, **clear the stale flag and resolve it** (5a). Never leave a now-answerable question hanging,
  and never justify it with the `track_close` gate — that gate is for work threads, an answered
  open question is the allowed close.
- **Process only `status: active` open questions** whose last attempt isn't already today's
  (the per-question attempt log — see below — makes a same-day re-run a no-op).
- On demand: the operator says "разбери открытые вопросы / try to close the open questions".

## Algorithm — per open question

> Cognitive, one question at a time. No regex matching. Load the client's full state first
> (mm_update Step 2) so the answer is interpreted in context.

For each active `type: open_question` across `state_ops` clients:

1. **Read the question** — `title`, `assist.hypothesis`, `next_action`, `assist.actions[]`.
   The hypothesis/next_action usually already name the source and key (e.g. "ЕГРИП-выписку
   по ИНН 500100732259", "PDF договора № 63 стр. 1-2", "1С → Контрагенты → Договоры").

2. **Classify the rung** (`mm_update/SKILL.md § Derive before asking`):
   - **Rung 1 — zero-touch.** Answer is in a connected source: a file in the client's
     Drive/Accounting folder, another `state/*.json`, a collector report already pulled.
   - **Rung 2 — one-tap.** Answer needs a **read-only fetch the runtime performs itself**:
     a registry lookup by a known key (`egrul` by INN), a `1c` contract/account read, an
     `ofd` record, a bank statement (`tbank`/`alfabank`). Even when it drives a browser this
     is *acquisition*, gated only as `browser_action` if the safety config demands — it is
     not a question for a human.
   - **Rung 3 — needs a human.** Input only a person holds (how many employees, which 1C,
     client consent), a judgment, or an outbound/irreversible act. **Do not fetch.** Skip
     here; optionally hand to `§ Batch the human questions` below.

3. **Attempt the read** (rung 1 & 2 only). Run the matching workflow with the key from the
   question: `connectors/egrul/…` (by INN/OGRNIP), `connectors/ofd/…`, `connectors/tbank/…`
   / `alfabank`, the Drive read for a named file, the 1C reads (when 1C is connected;
   `one_c` is paused — if so, leave the question for the operator and say why). Resolve the
   client's jurisdiction first (INSTRUCTIONS §0) — a non-RU client uses that pack's portals
   (e.g. Coretax/Drive), never the RF defaults.

4. **Evaluate the result against the confidence gate** (mm_update Confidence):
   - **High & objective** — the source gives one unambiguous answer (ОКВЭД list from the
     EGRIP extract; issuing bank from the statement footer; contract terms from the PDF).
     → **Apply + close** (step 5a).
   - **Medium / partial** — a finding, but it needs the accountant's eyes, or the source was
     only partly conclusive. → **Apply what's certain + surface, do not close** (step 5b).
   - **Failed / inconclusive / needs a credential** — the fetch returned nothing usable, hit
     a captcha/credential wall, or the source doesn't actually contain the answer. → **Leave
     the question, record the attempt, downgrade to rung 3** with a precise reason
     ("ЕГРИП требует капчу — нужен оператор" / "договор не найден в 1С — спросить клиента").

5. **Write the outcome** (always via `state_ops`/`_tracks`, never by hand; backups + UTF-8
   are built in):
   - **5a. Apply + close.** Write the fact to the right `state/*.json`
     (`accounts`/`identity`/`counterparties`/…). Then, because **an answered `open_question`
     is a clarification, not a work thread**, the daemon **may close it**:
     `_tracks.add_history_event(cid, qid, '<what was found + source>', source='<channel>:…',
     auto=True)` → `_tracks.update_status(cid, qid, 'done', reason='answered from <source>')`.
     Clear `next_action` and the stale `assist`. This is the one close a daemon is allowed —
     it is explicitly **not** the §D/`track_close` gate, which still governs real work
     threads (payments, filings) and stays operator-only.
   - **5b. Apply + surface (no close).** Write what is certain, refresh `next_action`/
     `assist.hypothesis` to state the finding ("Из ЕГРИП: 68.20, 70.22 — 77.39 НЕ заявлен;
     подтвердить добавление"), and leave `status` active so it shows in the overview
     **«🔄 Последние обновлённые / на подтверждение»** zone for a one-tap operator confirm.

6. **Audit + morning visibility.** One block per client in `journal/operator_decisions.md`
   (Confidence: high/medium, "auto-resolved overnight"). Then write the night summary into
   `journal/brief_<date>.md` (mm_update Step 7): "🌙 За ночь закрыто N вопросов (банк по
   выписке, ОКВЭД из ЕГРИП…); ещё M — на подтверждение; K — нужен ответ клиента." Every
   auto-applied fact carries a one-tap **undo** via the track card.

## Always log the attempt — the track history is the real audit trail

Every resolution attempt appends a history event to the open question — **including failures
and empty results**. The operator must be able to open a question and see what the system
tried and why it is still open, not silence. So on every pass, for every question it touched:

- **Resolved** → the event is already written in 5a/5b ("Из ЕГРИП: 68.20, 70.22 — записано",
  source `egrul:…`).
- **Nothing found / inconclusive / blocked** → append a plain-language event naming what was
  checked and the result: «Проверил 1С — нужный файл (договор с ООО «32») не найден»,
  «ЕГРИП недоступен — капча, нужен оператор», «Выписка прочитана — банк-эмитент в ней не
  указан». `source` is required (`question_resolver:1c`, `question_resolver:egrul`, …),
  `auto=True`.

This is the one place a "no-op" **is** worth recording, and it deliberately differs from
`mm_update`'s journal rule (`operator_decisions.md` logs only real changes, never no-op runs):
that file is the practice-wide audit narrative; **the track history is the per-question diary**
and must hold the misses too, so an unresolved question carries its own explanation instead of
reappearing each morning looking untouched.

**Anti-spam.** If tonight's outcome is identical to the last attempt's, do not duplicate the
full event — append a terse repeat («1С проверено повторно — без изменений, файл не найден,
попытка 3») or bump the latest note. A real log, not a flood.

Event text is operator-facing → **100% in the operator's configured locale (`instance.locale`), no stray English, no machine annotations**
(INSTRUCTIONS §0.1 / §0.1.a). Writes only the existing `history[]` field → no schema change,
no migration.

## Confidence is the brake

When in doubt, **5b not 5a**. A wrong auto-close is worse than a surviving question: it hides
a mistake behind a green check. Close only when the source is authoritative (a government
registry, the bank's own statement, a signed contract) and the answer is singular. Anything
interpreted, estimated, or reconciled across sources → surface for confirmation.

## Batch the human questions (rung 3) — optional, outbound-gated

The rung-3 remainder is often many "ask the client/Полина" questions for one client
(onboarding clients especially). Instead of leaving N separate cards, the daemon may compose
**one** data-request draft (template `workflows/templates/data-request-template.md`) that
bundles them, and attach it to the client for the operator to review and send. Sending is an
**outbound** action — the daemon drafts, the **operator approves and sends** (safety
`external_sends` gate). Never send autonomously.

## Safety (inherits `policies/safety-rules.md §5a`)

- **Reads need no approval** — acquisition (Drive/registry/1C/OFD/bank reads) is the daemon's
  job, applied directly via `state_ops`.
- **Closing** — allowed **only** for answered `type: open_question` clarifications (5a). Work
  threads (payments, filings, anything client-promised) are never closed by the daemon.
- **Outbound stays gated** — any message/filing to a client or authority is drafted only;
  the operator sends.
- **Browser fetches** — read-only registry/portal lookups are acquisition; if the safety
  config gates `browser_actions`, run them as the approved nightly job, not per-question.
- Credentials/PINs/captcha → stop, downgrade to rung 3, name the blocker for the operator.

## Deployment note (lands on the operator's machine by pulling the engine)

This skill writes only **existing** fields (state files + track `status`/`history`), so it
ships as **engine files — no data migration** (no schema change). The
operator upgrades by pulling the engine; the scheduled `resolution_sweep` run then applies this
logic to *their* live questions on *their* data (it is not "fixed" by hand in any snapshot).
There is no separate job to register — it rides the `resolution_sweep` cron
(`connectors/scheduler/SKILL.md`). If we later record per-question resolution telemetry as new fields, **that** is a
migration (`migrations/NNNN_*.py`).

## Related

- `connectors/mm_update/SKILL.md` — the rung logic + write API this daemon executes.
- `policies/safety-rules.md §5a` — reads-no-approval / close model / outbound gate.
- `policies/INSTRUCTIONS.md §0` — resolve jurisdiction before choosing a portal.
- `connectors/{egrul,ofd,tbank,alfabank}/` + the Drive/1C reads — the acquisition workflows.
- `tests/runtime_scenarios/` — S5 is the gate for this behaviour.
