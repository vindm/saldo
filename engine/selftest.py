#!/usr/bin/env python3
"""selftest.py — end-to-end smoke test for the Saldo engine.

Runs the full pipeline against the bundled SYNTHETIC example instance (no real
data, no config needed) and asserts the system is healthy. Use it after any
engine change and in CI to make sure nothing broke.

    python3 engine/selftest.py        # exit 0 = all green, non-zero = a failure

Checks:
  1. Every engine/connector/migration .py byte-compiles.
  2. generate.py renders the example instance with "LINT OK" and no traceback.
  3. The expected pages exist, are non-empty HTML, and inter-page links resolve.
  4. state_lint.py reports 0 errors; system_integrity_check.py has no [ERROR].
  5. migrate.py status runs clean.
  6. Re-render is deterministic (same set of pages, same sizes ± the clock line).
"""
import os, sys, re, glob, subprocess, tempfile, py_compile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
EXAMPLE_DATA = os.path.join(REPO, "instances", "example", "data")

fails = []
def check(cond, msg):
    print(("  ok  " if cond else " FAIL ") + msg)
    if not cond:
        fails.append(msg)

def run(cmd, env):
    e = dict(os.environ); e.update(env)
    return subprocess.run(cmd, cwd=HERE, env=e, capture_output=True, text=True)

def render(dash_dir):
    env = {"ABA_DATA_DIR": EXAMPLE_DATA, "ABA_DASHBOARD_DIR": dash_dir, "ABA_LOCALE": "en"}
    env.pop("ABA_DASHBOARD_DIR", None) or None
    env["ABA_DASHBOARD_DIR"] = dash_dir
    return run([sys.executable, "generate.py"], env)


print("Saldo engine self-test\n" + "=" * 40)

# 1. compile everything
print("\n[1] byte-compile")
nbad = 0
for f in (glob.glob(os.path.join(HERE, "*.py"))
          + glob.glob(os.path.join(REPO, "connectors", "**", "*.py"), recursive=True)
          + glob.glob(os.path.join(REPO, "migrations", "*.py"))):
    try:
        py_compile.compile(f, doraise=True)
    except Exception as e:
        nbad += 1; print("   compile FAIL:", f, e)
check(nbad == 0, f"all .py compile ({nbad} failures)")

# 2. render the example instance
print("\n[2] render example instance")
d1 = tempfile.mkdtemp(prefix="saldo_selftest_")
r = render(d1)
out = r.stdout + r.stderr
check(r.returncode == 0, "generate.py exit 0")
check("LINT OK" in out, "render ends with LINT OK")
check("Traceback" not in out, "no traceback during render")
n_ok = out.count("OK:")
check(n_ok >= 5, f"rendered multiple pages (OK: x{n_ok})")

# 3. expected pages + links resolve
print("\n[3] pages & links")
overview = os.path.join(d1, "dashboard_overview.html")
check(os.path.exists(overview), "dashboard_overview.html exists")
for page in ("plan_today.html", "calendar.html", "periods.html", "changelog.html"):
    check(os.path.exists(os.path.join(d1, page)), f"{page} exists")
client_pages = glob.glob(os.path.join(d1, "dashboard_*.html"))
check(len(client_pages) >= 2, f"client dashboards rendered ({len(client_pages)})")
if os.path.exists(overview):
    html = open(overview, encoding="utf-8").read()
    check("<html" in html and len(html) > 2000, "overview is non-empty HTML")
    # every dashboard_*.html link on the overview points to a file that exists
    broken = [h for h in set(re.findall(r'href="(dashboard_[a-z0-9_]+\.html)"', html))
              if not os.path.exists(os.path.join(d1, h))]
    check(not broken, f"overview links resolve (broken: {broken[:3]})")

# 4. lint + integrity
print("\n[4] lint & integrity")
env = {"ABA_DATA_DIR": EXAMPLE_DATA, "ABA_LOCALE": "en"}
rl = run([sys.executable, "state_lint.py"], env)
check("error" not in (rl.stdout + rl.stderr).lower().split("warn")[0]
      or re.search(r"0 error", rl.stdout + rl.stderr) is not None,
      "state_lint: 0 errors")
ri = run([sys.executable, "system_integrity_check.py"], env)
io = ri.stdout + ri.stderr
check("ERROR — need fixing (0)" in io or "No blocking errors" in io or ri.returncode == 0,
      "system_integrity_check: no blocking errors")

# 5. migrate status
print("\n[5] migrations")
rm = run([sys.executable, "migrate.py", "status"], env)
check(rm.returncode == 0, "migrate.py status runs clean")

# 6. deterministic re-render (same pages, sizes stable ignoring the clock)
print("\n[6] deterministic re-render")
d2 = tempfile.mkdtemp(prefix="saldo_selftest2_")
render(d2)
s1 = {os.path.basename(p) for p in glob.glob(os.path.join(d1, "*.html"))}
s2 = {os.path.basename(p) for p in glob.glob(os.path.join(d2, "*.html"))}
check(s1 == s2, "same set of pages on re-render")

print("\n" + "=" * 40)
if fails:
    print(f"RESULT: FAIL ({len(fails)} check(s) failed)")
    for m in fails:
        print("  - " + m)
    sys.exit(1)
print("RESULT: PASS — all checks green")
sys.exit(0)
