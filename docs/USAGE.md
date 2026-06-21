# Usage — getting started, daily flow, and updating

This is the "how do I actually run and use it" guide. For the design, see [`ARCHITECTURE.md`](ARCHITECTURE.md); for installing onto an existing practice, see [`MIGRATION.md`](MIGRATION.md); for the in-app manual, open **How to use** in the dashboard sidebar (`guide.html`).

The system is a **static dashboard generator + an AI assistant**. There is no server: a Python script reads the practice's `state/*.json` and writes HTML files you open in a browser. The "intelligence" is the assistant (Cowork / Claude) that keeps `state` up to date and drafts work; the engine only renders.

---

## 1. New user — download & connect to Cowork

Audience: someone who is **not** the original practice and wants to adopt the product.

1. **Get the code.** Clone or download the repo to a local folder, e.g. `~/ai-bookkeeping-assistant`.
2. **See it run on synthetic data first.**
   ```bash
   cd ~/ai-bookkeeping-assistant
   pip install pyyaml
   cp config/instance.example.yaml config/instance.yaml
   python3 engine/generate.py
   open instances/example/data/dashboards/dashboard_overview.html
   ```
   This renders the bundled **example instance** — entirely fabricated clients, no real data.
3. **Connect the folder to Cowork.** In the Claude desktop app (Cowork), add `~/ai-bookkeeping-assistant` (and your private data dir) as a workspace folder. The assistant can now read the policies/workflows and run the generator for you.
4. **Create your own instance.** Make a private data dir **outside the repo** (e.g. `~/my-practice-data`) following the layout in [`MIGRATION.md` §D](MIGRATION.md#d-data-layout-what-datadir-must-contain), point `config/instance.yaml`'s `data.dir` at it, and set `locale` + `brand`.
5. **Tell the assistant what you want done** — e.g. "run the morning routine", "draft the payment-order reminders for clients due on the 25th", "close this open question". The assistant edits `state`, you approve, it regenerates the dashboard.

> The assistant operates under a strict safety model: it acts only on operator commands, treats text inside incoming tasks/emails/docs as data (never instructions), and asks for approval before any state write, client message, or browser action. See [`policies/safety-rules.md`](../policies/safety-rules.md).

---

## 2. Daily flow (the operator's routine)

Open **How to use** in the dashboard for the full version. In short:

- **Morning:** open **Dashboard** (stats, brief, open questions, top-5, digest) → open **Plan** → work the top **Operations** (a whole operation can be processed as one batch) → tell the assistant "close / defer / do this".
- **Start / end of month:** open **Periods** to see where each reporting month stands across the 6 pipeline stages; click a lagging stage to jump to that operation on the Plan. Use **Calendar** for tax dates.
- **During the day:** signals (Telegram/email) appear in the digest; a thought about a client → **Dictate** → paste into the assistant chat.

What is **not** a task (so the Plan stays clean):
- **Open questions / clarifications** → the Dashboard "Open questions" block.
- **Passive waits / monitoring** (nothing to do but wait) → the Plan's collapsed "Waiting" lane.
- **Risks** → the client card.

---

## 3. Updating to a new version (pull + re-integrate)

Because **data lives outside the repo**, upgrading the engine never touches your data.

1. **Back up / snapshot** first (cheap insurance):
   ```bash
   python3 engine/snapshot.py pre-update     # if available, or just copy your data dir
   ```
2. **Pull the new engine.**
   ```bash
   cd ~/ai-bookkeeping-assistant
   git pull          # or replace the folder with the new release
   pip install -r requirements.txt   # if dependencies changed (at minimum: pyyaml)
   ```
   Your `config/instance.yaml` and your private `data.dir` are untouched (the repo's `.gitignore` keeps them out of version control).
3. **Re-render and re-check.**
   ```bash
   python3 engine/generate.py
   python3 engine/state_lint.py        # must exit clean
   ```
   Open the dashboard and confirm everything renders. If a new version changes a data shape, the release notes / [`ROADMAP.md`](ROADMAP.md) will say so and any migration step ships as a script in `tools/`.
4. **If the data schema changed**, run the indicated `tools/` migration against a **copy** of your data dir first, diff the dashboards, then point `config/instance.yaml` at the migrated dir.

The golden rule for upgrades: **engine and data are separate.** Pull the engine freely; transform data only with an explicit, reviewed `tools/` script against a copy.

---

## 4. Verifying a run

After any `generate.py` run:

- `state_lint.py` exits clean (no dangling tracks / cross-link gaps).
- The overview, plan, calendar, periods, and every client card open with no missing-link errors.
- A daemon file being absent logs a benign `… missing` line — that's graceful degradation, not a failure.
