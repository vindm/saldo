# Checklist: client reminder

Applies when clicking the "🔔 Remind" prompt in the dashboard, or when we see an open request in `request_log.md` with status `waiting` older than 5 days. The goal — bring the client back into communication without pressure, keeping a professional tone.

## Stage 1. Find a reason

- [ ] Open `_Planning/_registries/request_log.md`, find rows with status `waiting` sent more than 5 days ago
- [ ] In parallel — `clients_data.json[client].monthly_check.sources[*]` with status `gap` or `wait` and no recent client reply (field `last` older than 5-7 days)
- [ ] Identify **one** specific reason. Don't combine several requests into one reminder — the specificity is lost

## Stage 2. Read the backstory

- [ ] The Finkoper task chat for this client (via Claude in Chrome) or the corresponding email thread
- [ ] Understand:
  - What was already said in the original request
  - What the last contact with the client was, and in what tone
  - Whether the client was even available in that period (vacation, illness, holidays — possible legitimate reasons for the delay)
- [ ] If the `client-card.md` notes a "convenient contact time" or specifics — take them into account

## Stage 3. Choose tone by elapsed time

- **First reminder (5-7 days)** — soft, polite. "I wanted to check whether it's convenient to send…".
- **Second reminder (10-12 days)** — neutral, factual. "A reminder that to close {period} we need…". Specify a concrete new deadline.
- **Third reminder (>14 days)** — stop. We don't write on our own. **Escalate to the supervisor** — inform the manager that the client hasn't responded for 2 weeks, the consequences for reporting, and ask for intervention.

## Stage 4. Compose the text

- [ ] Use `templates/data-request-template.md` Template 1 (if the same primary documents are needed again) or Template 2 (if supporting documents are needed)
- [ ] Structure:
  1. Greeting
  2. Reference to the previous request ("A reminder about the request from {date}")
  3. What specifically we're waiting for
  4. New deadline (soft or hard — per Stage 3)
  5. Where to send it
- [ ] **No emotion.** Not "unfortunately", "it's a pity", "this worries me" — a neutral professional tone
- [ ] **No pressuring phrasing.** Not "urgent!", "I don't understand why you're not responding", "without this we can't do anything". If the elapsed time is critical — state the concrete risk (report overdue, FTS penalty with a cited article)

## Stage 5. Approval and sending

- [ ] Show the text to the operator in the format `### REMINDER {client}, {channel}:` (per INSTRUCTIONS.md Step 5)
- [ ] Get "send". Per `safety_rules.md §3/§4` — sending only with an explicit "send" in the chat
- [ ] Send:
  - To the Finkoper task chat — via Claude in Chrome per `templates/chrome-instruction-template.md`
  - To email — via Claude in Chrome (draft in email + approval + "Send" button)
  - To WhatsApp/Telegram — only through the operator manually; the bot doesn't go there

## Stage 6. Recording

- [ ] Update the row in `_registries/request_log.md`:
  - Reminder date in the comment
  - If older than 14 days and an escalation was made — status `🟡 escalated`, comment "escalated to the supervisor {date}"
- [ ] If a reply arrives within 24 hours of the reminder — status `🟢 received` + date, move to processing
- [ ] Entry in `_Planning/SP {Surname}/history.md` per the `templates/history-template.md`, type = `request` (repeat)

## What NOT to do

- Don't remind more than once every 5-7 days — it pressures and damages the relationship.
- Don't use emotional phrasing ("really need it", "it's burning", "we can't do anything without you").
- Don't go into self-directed escalation past 14 days without the operator's sign-off — the third reminder should be initiated by the supervisor.
- Don't combine several different requests into one reminder — the client will miss part of it.
- Don't send a reminder on weekends or outside the client's working hours if the card notes constraints.
- Don't duplicate a reminder across 2-3 channels at once (Finkoper + email + WhatsApp) — it reads as pressure.
