import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_CFG_PATH = os.path.abspath(os.path.join(_HERE, "..", "config", "instance.yaml"))
_CFG_DIR = os.path.dirname(_CFG_PATH)


def _load_cfg():
    """Load config/instance.yaml once (optional; tolerate missing pyyaml/file)."""
    try:
        import yaml  # optional
        with open(_CFG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


_CFG = _load_cfg()


def _resolve(p, base):
    """Absolute path stays; relative is resolved against `base`."""
    if not p:
        return None
    return p if os.path.isabs(p) else os.path.abspath(os.path.join(base, p))


# ── Data dir. Resolution order:  env ABA_DATA_DIR  ->  config [data].dir
#    (relative paths are resolved against the config/ directory)  ->  bundled example.
_data_cfg = _resolve((_CFG.get("data") or {}).get("dir"), _CFG_DIR)
DATA_DIR = (
    os.environ.get("ABA_DATA_DIR")
    or _data_cfg
    or os.path.abspath(os.path.join(_HERE, "..", "instances", "example", "data"))
)

# ── Dashboard output. Resolution order:  env ABA_DASHBOARD_DIR  ->
#    config [data].dashboards_dir (relative to config/)  ->  DATA_DIR/dashboards.
# Default: dashboards live INSIDE the data dir, so a practice folder is
# self-contained (clients/ + journal/ + brand/ + dashboards/) and inter-page
# links resolve next to the data they render from.
_dash_cfg = _resolve((_CFG.get("data") or {}).get("dashboards_dir"), _CFG_DIR)
DASHBOARD_DIR = (
    os.environ.get("ABA_DASHBOARD_DIR")
    or _dash_cfg
    or os.path.abspath(os.path.join(DATA_DIR, "dashboards"))
)


# ── Brand (config-driven; was hardcoded in the engine). Resolution order:
#    env vars  ->  config/instance.yaml [brand]  ->  neutral defaults.
def _load_brand():
    name, tagline, monogram = "Example Practice", "bookkeeping services", "EP"
    b = (_CFG.get("brand") or {})
    name = b.get("name", name)
    tagline = b.get("tagline", tagline)
    monogram = b.get("monogram", monogram)
    name = os.environ.get("ABA_BRAND_NAME", name)
    tagline = os.environ.get("ABA_BRAND_TAGLINE", tagline)
    monogram = os.environ.get("ABA_BRAND_MONOGRAM", monogram)
    return name, tagline, monogram


BRAND_NAME, BRAND_TAGLINE, BRAND_MONOGRAM = _load_brand()


# ── Locale (data-token layer; see _vocab.py). Resolution order:
#    env ABA_LOCALE  ->  config/instance.yaml [instance].locale  ->  'en'.
def _load_locale():
    locale = (_CFG.get("instance") or {}).get("locale", "en")
    locale = os.environ.get("ABA_LOCALE", locale)
    locale = (locale or "en").strip().lower()
    if locale not in ("en", "ru"):
        locale = "en"
    return locale


LOCALE = _load_locale()
