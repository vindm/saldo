# Atomic skill: check_notifications

Open the Finkoper notification bell ("Notification of new tasks") and return fresh signals.

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `since` | ISO datetime | `null` (if set — only notifications after it; if `null` — all visible in the bell) |
| `include_old_tasks` | bool | `false` (if `false` — filter out notifications about tasks created before 2026-04-01) |

## Algorithm

1. Via Claude in Chrome, open Finkoper, click on the notification bell.

2. Get the list of notifications with fields:
   - `notification_id` (if present) or sequence number
   - `datetime` — when it arrived
   - `type` — `task_new` / `task_updated` / `task_closed` / `chat_message` / `mention`
   - `entity_id` — task / chat id
   - `entity_url`
   - `text_preview` — notification text

3. Apply the `since` filter — keep only newer ones.

4. If `include_old_tasks=false` — for task notifications, filter out those whose `entity_id` refers to tasks that started before 2026-04-01 (by reconciling with `latest/tasks.json` or by opening the task).

5. **Do not mark notifications as read.** Per `sync_protocol.md` — we only look, we don't "reset" the bell.

## Return format

```json
{
  "notifications": [
    {
      "datetime": "2026-05-16T07:30:00",
      "type": "task_closed",
      "entity_id": "26135860",
      "entity_url": "https://app.finkoper.com/tasks/26135860",
      "text_preview": "Task completed: SP Client A..."
    }
  ],
  "count": 1,
  "filters_applied": {"since": "2026-05-15T22:05", "include_old_tasks": false}
}
```

## Safety

- **Do not mark notifications as read** — this masks the signal for other runs and other eyes. See `sync_protocol.md`.
- Read-only.

## When it is called

- `morning_full_scan.md` — to reconcile with the task diff.
- `incremental_update.md` — the main entry point: "is there anything new since last_run".
- Me in-session, triggered by "what's new overall" (`since=last_run`).

## Limitations

- If the bell shows "No new events" — return an empty array + the flag `empty=true`.
- The text in the bell is truncated. Full event text — via `read_task` / `read_chat`.

---

## UI map (current as of 2026-05-24)

In the Finkoper header there are **three** `[class*="HeaderNotification_root"]` icons:

1. **Kontur.Extern** — a separate service, usually empty.
2. A service one (always without a counter — we skip it).
3. **"Events / Tasks"** — the main bell, which has a badge with the number of unread tasks.

The needed bell is determined not by position, but by the presence of a child element `[class*="HeaderNotification_count"]` with a number > 0.

### Optimized pipeline (1 turn instead of 5–10)

```js
// 1) Find the bell with a non-empty counter
const target = [...document.querySelectorAll('[class*="HeaderNotification_root"]')]
  .find(b => {
    const cnt = b.querySelector('[class*="HeaderNotification_count"]');
    return cnt && parseInt(cnt.innerText.trim()) > 0;
  });

// If none — the bell is empty
if (!target) ({ empty: true, notifications: [], count: 0 });
else {
  // 2) Click, wait for the popover, switch to the "Tasks" tab, read
  target.querySelector('button').click();
  await new Promise(r => setTimeout(r, 1500));
  const popover = [...document.querySelectorAll('[class*="HeaderNotification_popupWrapper"][class*="isShow"]')]
    .find(el => el.innerText.includes('События')); // 'События' = 'Events' (Finkoper UI label)
  const tab = [...popover.querySelectorAll('.Tabs_tab__eDmaF')].find(t => t.innerText.includes('Задачи')); // 'Задачи' = 'Tasks' (Finkoper UI tab)
  if (tab) tab.click();
  await new Promise(r => setTimeout(r, 1000));
  // parse popover.innerText in the format:
  // "HH:MM   DD.MM.YYYY\nNew task\nClient\nPreview..."
}
```

Wrap it into **one** `browser_batch` using the template `navigate → wait → JS-expert → wait → JS-read`. Do not split it into 5–10 single calls.

### What NOT to do

- ❌ Don't click all three bells in a row "just to look".
- ❌ Don't open the popover if the counters are 0 — an empty popup adds nothing.
- ❌ Don't mark as read (see Safety above).

---

_Version 1.0 — 2026-05-16._
