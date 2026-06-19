# `news` domain skills

> Collecting current accounting news on topics relevant to the operator's clients (USN / patent regime / insurance contributions / 54-FZ / reporting). Fewer files than finkoper and email — news has no "entities" (tasks / letters), only topics and filters.
>
> **These skills are invoked by:**
> - The daemon `Scheduled/news/SKILL.md` — in the morning (`morning_full_scan`)
> - Me in a session — on the operator's trigger ("what's new on USN" / "is there any news about 54-FZ")
> - The updater on T5 (news with an explicit deadline/penalty) — checks applicability to clients

## Skills

| File | Type | What it does |
|---|---|---|
| [`search_topics.md`](search_topics.md) | atomic | Web search for news on a single topic over a period |
| [`morning_full_scan.md`](morning_full_scan.md) | composite | Morning sweep of all relevant topics + categorization + daily report |
| [`incremental_update.md`](incremental_update.md) | composite | News since last_run — appends to the daily report |

## Search topics (filter for full_scan)

| Topic | Key sources | Relevance |
|---|---|---|
| Tax Code changes / government decrees | nalog.gov.ru, consultant.ru, garant.ru | all clients |
| Letters from the tax authority (FTS) / Ministry of Finance / social fund (SFR) | nalog.gov.ru, minfin.gov.ru | all |
| USN (income 6%) | klerk.ru, buh.ru, glavbukh.ru | all 6 clients |
| Patent (patent regime) | klerk.ru, buh.ru | Client A, Client A (when there is a patent) |
| SP insurance contributions | klerk.ru, buh.ru, nalog.gov.ru | all |
| Single tax account (ENS) / notifications | klerk.ru, buh.ru | all |
| 54-FZ / online cash registers / OFD | klerk.ru, buh.ru, kkt.nalog.gov.ru | Client A (2 registers), Client A (registering), Client A (potentially) |
| Statistical reporting to the statistics portal | gks.ru, websbor.gks.ru | Client A (definitely), the rest (check annually) |
| EDI / electronic reporting | klerk.ru | all |
| **Excluded:** UKEP / electronic signature (ECP) / qualified e-signature (KEP) | — | not the operator's area (see `memory/ukep_not_my_zone.md`) |

## When to invoke which

| Trigger | Skill | Parameters |
|---|---|---|
| "is there any news about X" | `search_topics.md` | `topics=["X"], since=24h ago` |
| "what's new in accounting today" | `morning_full_scan.md` | `today=today, lookback_hours=24` |
| "update the news" | `incremental_update.md` | `since=last_run` |
| "rebuild the news" | `morning_full_scan.md` | — |

## Invocation format

Same as `finkoper/` and `email/`:

```
1. Read `connectors/news/search_topics.md`. Execute with:
   topics = ["USN", "SP insurance contributions"]
   since = <24h ago>
   max_results_per_topic = 10
   Get `news_items[]` with metadata.

2. Categorization in the composite → daily report.
```

## Security

- Web-fetch only from trusted sources (see the topics table).
- UKEP / electronic signature (ECP) news — skip.
- Do not store raw HTML, only structured summaries.

## History

- **2026-05-16** — refactored from the monolithic `Scheduled/news/SKILL.md` (58 lines) into a decomposition of 3 files + README. P4-news.

---

_Folder created 2026-05-16 as part of P4._
