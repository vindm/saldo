# Convention: single-account chat collector (by_chat)

Shared protocol for browser-driven messengers where **one operator account** holds a separate
chat per client — **Telegram, WhatsApp, Max**. There is no account to switch (`switch: none`,
`serves: by_chat`); the fan-out unit is the **endpoint** — a conversation, a shared work channel, or a person who acts for the client (assistant / accountant). Each provider skill
(`connectors/{tg,whatsapp,max}/`) supplies only its deltas (web URL, session check, handle
format, quirks) and inherits everything below.

## Shared model

- **One operator account** per messenger (`config → sources.<svc>`, `switch: none`,
  `access: auto` once linked). **Access is session-level only** — the one question is *is the
  operator's account logged in?* Individual chats/channels have **no per-chat `cred_status`**:
  they're reachable by search (username / phone / peer-id) the moment the session is up. A client
  `quick_access` `service: tg|whatsapp|max` entry is a **routing pointer, not a credentialed
  access point** — ignore any `cred_status` on it (no «уточнить»). Nothing per-chat to request.
- **endpoint set** = the client communication graph `behavior.channels.endpoints[]`
  (migration 0028) filtered to `transport: <svc>` AND `sync: true`. 🔴 **A client is NOT one
  chat.** It can have a personal DM (`role: client`), shared **work channels** (`role:
  work_channel` — e.g. a payment-reports or documents feed) and **people who act for them** — an
  assistant or an outsourced accountant (`role: assistant | accountant`). **Read EVERY such
  endpoint, not only the personal DM** — that is the whole point of the graph; the old behaviour
  (personal chat only) silently dropped channels and assistants. Each endpoint carries its handle
  (`@username`) / `peer_id` and its `role`. Endpoints mapping to no chat are **ignored**.
  (Back-compat: a client with no `endpoints[]` yet falls back to the `primary`/`secondary`
  `type: <svc>` channel as a single `role: client` endpoint.)
- **Per-endpoint watermark** in `journal/<svc>_state.json`: the personal DM keeps the
  **client-id** key (back-compat); every other endpoint is keyed by its **endpoint id**
  (`<svc>:@handle` / `<svc>:<peer_id>`):
  `{ <key>: {last_message_id, last_ts, last_read_at, unread_count} }`.

## Shared algorithm

1. Open the provider's web app; **verify the session is logged in** — else **flag + stop**
   (linking is human-gated: the operator logs in / scans the QR). Reading is `auto` afterward.
2. Build the **endpoint set** — every `endpoints[]` entry with `transport: <svc>` and `sync: true`, across all clients (a client without a graph falls back to its `primary`/`secondary` `type: <svc>` channel).
3. **Detect new without opening — the watermark is the ONLY authority.** For each **endpoint**
   (personal DM, work channel, assistant — all of them), compare the chat's **last-message
   timestamp / id from the chat list** against that endpoint's watermark in
   `journal/<svc>_state.json` (`last_ts` / `last_message_id`, keyed per the model above). A chat is "new" **iff
   its last message post-dates the watermark** — i.e. Saldo itself has not read past it. Open every
   such chat (most days, few or none).
   🔴 **The unread badge is NOT a "nothing-to-do" signal and must never gate the scan out.** The
   badge reflects whether a *human* has eyeballed the chat in some Telegram client — **Mom may have
   opened and read the message on her phone, clearing the badge** — while Saldo's watermark is
   unchanged and the message is still **unprocessed** (no track, no state written). Absence of a
   badge ≠ processed by Saldo. The badge / chat-list sort order are at most **hints that may ADD a
   candidate**; they may **never REMOVE one**. `last_read_at` / `unread_count` in state are
   Telegram's *read state*, kept for reference only — they are **not** the watermark and must not be
   used for detection.
   **When the chat-list timestamp is ambiguous** (same-day, can't tell if it post-dates the
   watermark, list throttled/virtualized) → **open the chat and compare `data-mid` to
   `last_message_id`**. When in doubt, **open** — never skip.
4. Read messages since the watermark. **Resolve the client's jurisdiction first**
   (INSTRUCTIONS §0) before interpreting.
5. Snapshot → `journal/inbox/<svc>_<date>.md` (one block per client; the engine source dot).
6. **mm_update inline** (`connectors/mm_update/SKILL.md`), `source='<svc>:<handle>:<date>'`, carrying the endpoint **role** so the write is attributed right — a message from the client's **accountant/assistant** or a **work channel** is *about* the client but is **not the client speaking** (the accountant filing a tax payment, a report dropped in the docs channel):
   action/question/promise → `upsert_track(type='<svc>_action_required')`; movement →
   `add_history_event`; **closing is operator-only (§D)** — on a confirmation, `add_history_event`
   + refresh `next_action` to «Подтвердить закрытие …», never `update_status('done')`.
7. Advance each processed **endpoint's** watermark (by its key); write `journal/inbox/<svc>_heartbeat.txt`.
8. **mm_update finale** (cross-link reconciliation, `resolves_when`, read-modify-write, lint,
   self-check, audit-log) + the **unconditional dashboard render**.

## Shared safety

- **Read-only.** No send/reply/react — outbound only on an explicit "send" from the operator in
  Cowork chat.
- **Mark-as-read caveat.** Opening a chat may mark it read in some web clients (WhatsApp, Max) —
  minimise by opening only chats the **watermark** (not the badge) says are new; note it as a known
  limitation. (Telegram `/a/` can preview without marking; provider skills state their behaviour.)
  Note the inverse risk too: a chat a human already read carries **no badge yet is unprocessed** —
  the watermark, not the badge, is what tells Saldo it still needs reading (step 3).
- Session linking is **human-gated**; reading is `auto` once linked. No QR/session data in state.

## Per-provider deltas (each skill specifies)

Web URL · how to verify the session is logged in · handle format (phone vs `@username`) ·
any mark-as-read side effect · provider quirks.

| Skill | Web app | Handle |
|---|---|---|
| `connectors/tg/sync.md` | `web.telegram.org/a/` | `@username` / peer id |
| `connectors/whatsapp/SKILL.md` | `web.whatsapp.com` | phone number |
| `connectors/max/SKILL.md` | `web.max.ru` | phone / `@username` |

## Atomic actions (single chat op, daemon or ad-hoc)

This file is the **sweep** (all chats, scheduled). For a **single** action — list chats, read
one chat, send a message — see `connectors/_chat_actions.md` (`list_chats` / `read_chat` /
`send_message`). The collector calls `read_chat` per conversation; the runtime calls these
directly when Mom asks ("check this chat" / "send a message"). `send_message` is outbound and
**approval-gated** — daemons never send.

## Related

- `connectors/_sources.md` — the by_chat granularity (single account, no switching).
- `connectors/_chat_actions.md` — the atomic list/read/send operations.
- `connectors/mm_update/SKILL.md` — the write path + §D close model.
