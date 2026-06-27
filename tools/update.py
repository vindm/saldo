#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""update.py - one-command updater for an operator's machine.

Does the whole "пулл -> миграции -> дашборды -> открыть" sequence so the operator
never touches a terminal: pull the latest engine from GitHub, apply any pending
state migrations to their data dir, regenerate the dashboards, and open today's
plan. Cross-platform; on Windows it is launched by tools/windows/update_saldo.bat
(itself behind a desktop shortcut), so the operator just double-clicks an icon.

Design note: the git pull happens HERE (in Python), not in the .bat. The .bat is
then a thin, stable launcher that never rewrites itself mid-run, and migrate.py /
generate.py are executed as fresh subprocesses that read the just-pulled code.

Flags (for testing / advanced use):
    --no-pull     skip git pull        --no-open   don't open the browser
    --no-pause    don't wait for Enter at the end
    --no-migrate  skip the migrate step (the runtime drives it stepwise)
    --no-generate skip the dashboard rebuild (the runtime regenerates after)
"""
import glob
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(REPO, "engine")

# Print UTF-8 even if the Windows console code page is legacy.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Locale-aware messages (operator-facing surface follows instance.locale).
try:
    sys.path.insert(0, ENGINE)
    from _config import LOCALE as _LOCALE
except Exception:
    _LOCALE = "en"


def say(en, ru):
    print(ru if _LOCALE == "ru" else en, flush=True)


def run(argv, label_en, label_ru):
    say("- " + label_en + " ...", "- " + label_ru + " ...")
    try:
        r = subprocess.run(argv, cwd=REPO)
        return r.returncode == 0
    except Exception as e:
        print("  " + str(e), flush=True)
        return False


def main():
    args = set(sys.argv[1:])
    py = sys.executable or "python"
    say("=== Updating Saldo ===", "=== Обновление Saldo ===")

    # 1. Pull the latest engine. Non-interactive (no y/n prompts) and self-healing:
    #    a normal fast-forward first; if that fails (e.g. Windows could not delete a
    #    restructured folder, or local drift), pin hard to the upstream and drop stray
    #    untracked files. Safe: data lives OUTSIDE the repo and config/instance.yaml +
    #    *.html are git-ignored, so `clean -fd` (no -x) never removes them.
    if "--no-pull" not in args:
        gitenv = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASK_YESNO="false")

        def clear_stale_locks():
            # A killed updater run (operator closed the window mid-pull) or an AV / sync
            # process holding a file leaves a *.lock under .git. Every subsequent git that
            # touches the index (pull / reset) then dies with "Unable to create index.lock".
            # The repair path below itself needs that lock, so it cannot recover - we must
            # remove the stale lock FIRST. Safe here: the updater is a single double-click
            # run with no concurrent git process, so any lock present is orphaned.
            gd = os.path.join(REPO, ".git")
            patterns = ["index.lock", "HEAD.lock", "config.lock", "shallow.lock",
                        os.path.join("refs", "**", "*.lock"),
                        os.path.join("logs", "**", "*.lock")]
            for pat in patterns:
                for lk in glob.glob(os.path.join(gd, pat), recursive=True):
                    try:
                        os.remove(lk)
                    except OSError:
                        pass

        def git(*a):
            try:
                # stdin=DEVNULL: if Git ever asks "Should I try again? (y/n)" (Windows
                # could-not-delete retry), it gets EOF and declines instead of looping.
                return subprocess.run(["git", "-C", REPO, *a], cwd=REPO, env=gitenv,
                                      stdin=subprocess.DEVNULL).returncode == 0
            except Exception as e:
                print("  " + str(e), flush=True)
                return False

        def rev(ref):
            try:
                r = subprocess.run(["git", "-C", REPO, "rev-parse", ref], cwd=REPO,
                                   env=gitenv, stdin=subprocess.DEVNULL,
                                   capture_output=True, text=True)
                return r.stdout.strip() if r.returncode == 0 else None
            except Exception:
                return None

        def up_to_date():
            h = rev("HEAD")
            return h is not None and h == rev("@{u}")

        say("- Downloading the latest version ...", "- Скачиваю свежую версию ...")
        clear_stale_locks()
        git("pull", "--ff-only")
        if not up_to_date():
            say("  (normal update did not apply - repairing to the latest version)",
                "  (обычное обновление не прошло - чиню до последней версии)")
            git("fetch", "origin")
            clear_stale_locks()  # the failed pull may have left a fresh stale lock
            git("reset", "--hard", "@{u}")
            git("clean", "-fd")  # leftover Windows-locked folders are harmless; ignore failure
        # Success is judged by HEAD matching upstream, NOT by exit codes: on Windows a
        # locked folder can fail to delete while HEAD still advanced correctly.
        if not up_to_date():
            say("  (could not update from GitHub - continuing with the current version)",
                "  (не получилось обновиться с GitHub - продолжаю на текущей версии)")

    # 2. Make sure Python dependencies are present (no-op if already installed).
    req = os.path.join(REPO, "requirements.txt")
    if os.path.exists(req):
        r = subprocess.run([py, "-m", "pip", "install", "--quiet", "-r", req], cwd=REPO)
        if r.returncode != 0:
            say("  (could not install Python packages - if there is an error below, run: pip install -r requirements.txt)",
                "  (не удалось установить пакеты Python - при ошибке ниже выполните: pip install -r requirements.txt)")

    # 2b. SAFETY: never silently rebuild the bundled DEMO on an operator machine.
    #     If there is no config/instance.yaml with a data.dir (and no ABA_DATA_DIR
    #     override), STOP - the engine would otherwise fall back to instances/example.
    if not os.environ.get("ABA_DATA_DIR"):
        cfg = os.path.join(REPO, "config", "instance.yaml")
        ddir = None
        if os.path.exists(cfg):
            try:
                import yaml
                ddir = ((yaml.safe_load(open(cfg, encoding="utf-8")) or {}).get("data") or {}).get("dir")
            except Exception:
                ddir = None
        if not ddir:
            say("STOP: no config\\instance.yaml with data.dir - refusing to build the demo.",
                "СТОП: нет config\\instance.yaml с data.dir - чтобы не собрать демо вместо ваших данных.")
            say("  Create it (copy config\\instance.example.yaml, set data.dir + locale: ru) and re-run.",
                "  Создайте его (скопируйте config\\instance.example.yaml, укажите data.dir и locale: ru) и повторите.")
            if "--no-pause" not in args:
                try: input()
                except EOFError: pass
            return 1

    # 3. Apply pending data migrations (backup + atomic + ledger handled by migrate.py).
    #    --no-migrate: the runtime (connectors/migration_runtime) drives them stepwise.
    ok_mig = True
    if "--no-migrate" not in args:
        say("- Applying data migrations ...", "- Применяю миграции данных ...")
        rc = subprocess.run([py, os.path.join(ENGINE, "migrate.py"), "up", "--apply"],
                            cwd=REPO).returncode
        if rc == 2:
            # exit code 2 = a pending migration needs the stepwise runtime flow, which
            # this unattended updater cannot do (it has judgment + an approval pause).
            # Do NOT regenerate on half-updated data - hand off to the assistant.
            say("This update must be applied step by step. Open Saldo and say "
                "\"обнови Saldo\" so the assistant applies it with you.",
                "Это обновление нужно применить пошагово. Откройте Saldo и скажите "
                "«обнови Saldo» — ассистент применит его вместе с вами.")
            if "--no-pause" not in args:
                try: input()
                except EOFError: pass
            return 2
        ok_mig = (rc == 0)

    # 4. Regenerate the dashboards from state.
    ok_gen = True
    if "--no-generate" not in args:
        ok_gen = run([py, os.path.join(ENGINE, "generate.py")],
                     "Rebuilding the dashboards", "Пересобираю дашборды")

    # 5. Open today's plan.
    opened = False
    if "--no-open" not in args and ok_gen:
        try:
            from _config import DASHBOARD_DIR
            page = os.path.join(DASHBOARD_DIR, "plan_today.html")
            if os.path.exists(page):
                if sys.platform.startswith("win"):
                    os.startfile(page)  # noqa
                elif sys.platform == "darwin":
                    subprocess.run(["open", page])
                else:
                    subprocess.run(["xdg-open", page])
                opened = True
        except Exception:
            pass

    print(flush=True)
    if ok_gen:
        say("Done - dashboards are up to date." + ("" if opened else " Open plan_today.html to view."),
            "Готово - дашборды обновлены." + ("" if opened else " Откройте plan_today.html."))
    else:
        say("Something went wrong above. Send this window to Dima.",
            "Что-то пошло не так выше. Покажите это окно Диме.")

    if "--no-pause" not in args:
        try:
            input(("\nPress Enter to close..." if _LOCALE != "ru"
                   else "\nНажмите Enter, чтобы закрыть..."))
        except EOFError:
            pass
    return 0 if (ok_gen and ok_mig) else 1


if __name__ == "__main__":
    raise SystemExit(main())
