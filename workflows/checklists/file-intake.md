# Checklist — manually moving files into a client folder

A short 30-second self-check so a file doesn't end up in the wrong folder. Applies to **any** manual move (from Downloads, between client folders, from email to the drive, etc.) — by both the assistant and the operator.

## Self-check before `mv` / Drag & Drop

1. **Read the whole file name.** It usually says whose it is right in the name:
   - `Statements_SP CLIENT A_01.01.2026-31.03.2026.zip` → the client.
   - `PARTNER_ACT_<redacted>_*.pdf` → the client (the contract number with the aggregator).
   - `<redacted>__2026__04__01__2026__04__30.xlsx.zip` → last 4 digits of the settlement account (`<redacted>` → the client, `<redacted>` → the client, etc.).
   - If the name is anonymized (`document.pdf`, `statement.xls`, `IMG_xxxx.jpg`) — **open and look at the contents** before moving.

2. **Cross-check against the target folder.** Before you let go of the file — read out loud / in your head "folder `SP {surname}`" and compare it with the file name. Matches by surname — OK. Doesn't match — stop.

3. **Doubtful case — leave it in `<client doc folder>/`.** If the file is work-related but the client is undetermined — DON'T guess. Put it in `<client doc folder>/` and discuss.

4. **Duplicate (exists in both folders).** Not a move but an archive: `Archive/duplicates_<month>/`.

5. **Never delete.** Only move. When in doubt — `Archive/downloads_junk_<month>/`.

## When to apply

- Any operation of the kind "put a client's file into their folder".
- When sorting out Downloads (see INSTRUCTIONS.md section 5).
- When sorting files between client folders inside `WORK/`.

## If an error is discovered after the fact

(like the case of the client's ZIP statement in the client's folder, found by the `analytic` daemon on 13.05.2026, moved on 14.05.2026)

1. Don't panic — the file isn't deleted, just in the wrong folder.
2. Cross-check from both sides (source + target), make sure it isn't a copy.
3. Move it via `mv` (with approval if the assistant is doing it).
4. After the move — an entry in the client's `history.md`, so the track is preserved.
5. If it recurs — discuss whether to add a step to an earlier process (for example, to the Chrome-agent instruction template).

## History

- **XXXX-05-14.** Created after the case: the client's Q1 2026 ZIP statement sat in `a client/` from ~15.04 to 14.05 (~a month). Found by the `analytic` daemon on 13.05 as a 🟡 anomaly "another client's file in a client folder". Cause — a manual mix-up (the operator). Risk — posting the wrong client's bank data into 1C. The checklist is a preventive measure so the case doesn't recur.
