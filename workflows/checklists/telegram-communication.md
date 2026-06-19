# Checklist: Telegram communication with direct clients

Standard for working in the Telegram channel for the 9 direct clients. A supplement to safety rules section 3 (messengers).

## When we use Telegram at all

- Deliver a tax return to the client (.xml from Taxpayer LE)
- Deliver a single-tax-account (ENS) payment order to the client (details for payment)
- Request data from the client (bank, receipt, passport scan)
- Notify about an upcoming deadline (29.05 — fixed contributions)
- Answer a client's question

## What NOT to send via Telegram

- Passwords, keys, digital signatures — never
- Account details unencrypted, unless the client has confirmed the channel is secure
- A full bank statement (only totals / the needed lines)
- Personal data of third parties (employees, counterparties beyond the minimum)

## Safety rules (Telegram specialization)

| Action | Rule |
|---|---|
| **Reading a chat** | No approval needed (like Finkoper / email) |
| **Downloading an attachment** | No approval needed, into `CLIENTS/<client>/<month>/` |
| **Writing to a client** | **Only with an explicit "send"** in the Cowork chat |
| **Sending a return / payment order** | Approval of the final text + an explicit "send" |
| **Emoji and tone** | Business-like, no excessive familiarity; if the client uses informal address, that's acceptable |
| **Voice messages** | We don't leave them; we read incoming ones but transcribe only when necessary |

## Incoming-message work cycle

1. **In the morning at 06:45** — the `tg/morning_full_scan` daemon collects all new messages into `_diary/incoming/tg_<date>.md`.
2. **On the Dashboard / Plan** — messages with the marker `❓ needs a reply` go into the group **"💬 Requests — awaiting reply"** (but the other way around — it's **they** who are waiting on us, not us on them).
3. **On clicking 💬 Discuss** — a prompt with the message context is copied into the chat.
4. **I (the assistant) propose a reply** in the Cowork chat.
5. **The operator reviews** → says "send" → I prepare the final text for copying and prompt "open Telegram → @username → paste".
6. **After sending** — the operator writes "sent" in Cowork → I update the entry in `operator_decisions.md` (topic closed).

## Templates for typical messages (pending OK)

### Delivering a USN return
```
Hi! The USN return for 2025 is ready. The file is attached.
What to do:
1. Upload it to the FTS personal account (nalog.gov.ru → Documents section)
2. Sign with your UKEP
3. Submit
Deadline — by 30.04.2026. Ping me if anything.
```

### Delivering an ENS payment order
```
Hi! I've prepared a payment order for payment:
• Purpose: [text]
• Amount: X,XXX RUB
• KBK: [number]
• Payment deadline: DD.MM.YYYY

Details for paying into the ENS — see attachment / in the FTS personal account.
Please pay by [deadline] and let me know once you have.
```

### Requesting a statement
```
Hi! I need a statement for the main account for [month] for posting.
You can export it from the bank's personal account in PDF/Excel format and send it here.
Thanks!
```

### Deadline reminder
```
A reminder — [DD.MM] is the deadline for [what]. Amount [N RUB].
If you can't make it, let's discuss how to move it.
```

## What we update after the dialogue

- If the client sent data → post it into the KUDIR, update `monthly_check.sources[].status = 'ok'`
- If the client asked a question → don't close it until we've answered
- If the client closed the task → mark `status='ok'` in monthly_check
- If a new track arose (a long-running topic) → add it to the client's `mental_model.md`
- Everything goes into `operator_decisions.md` with a reference to the message date/time

## Related documents

- `_system/skills/tg/` — reading skills
- `_diary/tg_state.json` — last_seen state
- `_diary/incoming/tg_*.md` — daemon snapshots
- `_system/safety_rules.md` section 3
- `_aggregator.py` — the `tg` source
