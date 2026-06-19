# Atomic skill: news/search_topics

Web search for news on one or several topics over a given period.

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `topics` | string[] | **required** (e.g.: `["USN"]` or `["54-FZ", "online cash registers"]`) |
| `since` | ISO datetime | `24h ago` |
| `until` | ISO datetime | `now` |
| `max_results_per_topic` | int | `10` |
| `sources_filter` | string[] | `null` (if set — only these domains) |

## Sources

Preferred sources (in order of trust):
- **Official:** `nalog.gov.ru`, `minfin.gov.ru`, `gks.ru`, `consultant.ru`, `garant.ru`
- **Professional:** `klerk.ru`, `buh.ru`, `glavbukh.ru`, `pro.kontur.ru`

Do not use:
- Tabloid press
- Corporate blogs without verifiable references
- Foreign sources

## Algorithm

1. For each topic in `topics`:
   a) Build a search query: `<topic> site:<trusted domain> after:<since> before:<until>`
   b) Run a web search (via the WebSearch tool).
   c) From the results, keep only those published in the range `[since, until]`.
   d) Apply `sources_filter` if set.
   e) Filter out UKEP / electronic signature (ECP) / qualified e-signature (KEP) / e-signature certificates (filter by keywords in the headline/preview).
   f) Take up to `max_results_per_topic` of the most relevant.

2. For each result that passes, extract:
   - `title` — the headline
   - `url`
   - `source` — the publisher's domain
   - `published_at` — publication date
   - `preview` — the first 300 characters (snippet from the search)
   - `topic_tag` — which topic led to this result

3. Deduplicate by `url` (one news item could have matched two topics).

## Return format

```json
{
  "items": [
    {
      "title": "The tax authority (FTS) published clarifications on...",
      "url": "https://www.nalog.gov.ru/...",
      "source": "nalog.gov.ru",
      "published_at": "2026-05-15T...",
      "preview": "<300 characters>",
      "topic_tag": "USN"
    }
  ],
  "count": 1,
  "topics_searched": ["USN"],
  "sources_seen": ["nalog.gov.ru", "klerk.ru"],
  "skipped_ukep": 3,
  "filters_applied": {"since": "...", "until": "...", "max_per_topic": 10}
}
```

## When invoked

- `morning_full_scan.md` — for all topics from README.
- `incremental_update.md` — for all topics with `since=last_run`.
- Me in a session on the trigger "is there any news about X" — for a single topic.
- mm_update when analyzing a specific topic from the news stream (Updater/T5 deprecated 2026-05-24).

## Security

- Web search only via the `WebSearch` tool (Anthropic's trusted sources).
- Do not follow suspicious links (if the URL is not from the trusted list — skip it).
- UKEP / electronic signature (ECP) — filter by keywords.

## Limitations

- If nothing is found for a topic — return an empty `items` for that topic, do not crash.
- The search is performed in Russian; for English-language topics (international reporting) — skip (not our area).

---

_Version 1.0 — 2026-05-16._
