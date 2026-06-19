# Client & group profiles

The assistant separates **facts** (structured, for the deterministic engine) from **behavior** (prose, for the agent). Profiles are the behavior half.

## What is structured vs. prose

| Lives as | What | Read by |
|---|---|---|
| `instance.yaml` | runtime config: enabled connectors, brand, schedule, data dir | engine + scheduler |
| `state/*.json` | exact, auditable facts: requisites, regimes, amounts, deadlines, statuses | engine (renders them) + agent |
| **`group`** (one string per client, in `clients_index.json`) | the only structured field about organization — the UI groups clients by it | engine |
| **`profile.md`** (per client and per group) | interaction rules, tone, routing, escalation, special handling | the agent |

Rule of thumb: structure only what a deterministic program reads, or what must be exact and auditable (it's accounting). Everything the agent merely *acts on* is prose.

## The grouping label

Each client has one `group` (e.g. `team`, `direct`, or anything a practice invents — by region, by outsourcing company, etc.). The engine derives the set of groups from the clients themselves and renders one section/page per group. There is **no** hardcoded list of groups and no separate "group config layer."

Optional `tags: []` on a client are for cross-cutting filters (region, priority) and don't affect the primary grouping.

## Profiles are prose, nested like `CLAUDE.md`

Behavior is described in plain Markdown, exactly the way nested `CLAUDE.md` files work — the more specific one wins, and the agent reads them together. No merge logic in code.

```
data/
  groups/
    team/profile.md        # defaults for everyone in the "team" group
    direct/profile.md
  clients/
    <id>/profile.md        # this client's specifics — overrides the group profile
    <id>/state/*.json      # facts
    <id>/mental_model.md   # narrative
```

When the agent works a task for a client, it reads the group `profile.md` then the client `profile.md`; anything the client profile says overrides the group default. Because it's prose, "override" is just ordinary precedence the agent already understands — nothing to parse.

### Example

A `team` group profile says "no direct contact with the client — route through the company manager." A specific client's profile can override with "this client texts us directly, the manager approved it." The agent honors the client-level line. The engine doesn't care about any of this — it only sees `group: team` and puts the client in the Team section.

Templates: `workflows/templates/client-profile-template.md`, `workflows/templates/group-profile-template.md`.
