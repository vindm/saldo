import os

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("ABA_DATA_DIR") or os.path.abspath(
    os.path.join(_HERE, "..", "instances", "example", "data")
)
DASHBOARD_DIR = os.environ.get("ABA_DASHBOARD_DIR") or os.path.abspath(
    os.path.join(DATA_DIR, "..", "dashboards")
)


# ── Brand (config-driven; was hardcoded in the engine). Resolution order:
#    env vars  ->  config/instance.yaml [brand]  ->  neutral defaults.
def _load_brand():
    name, tagline, monogram = "Example Practice", "bookkeeping services", "EP"
    cfg_path = os.path.abspath(os.path.join(_HERE, "..", "config", "instance.yaml"))
    try:
        import yaml  # optional
        with open(cfg_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        b = (data.get("brand") or {})
        name = b.get("name", name)
        tagline = b.get("tagline", tagline)
        monogram = b.get("monogram", monogram)
    except Exception:
        pass
    name = os.environ.get("ABA_BRAND_NAME", name)
    tagline = os.environ.get("ABA_BRAND_TAGLINE", tagline)
    monogram = os.environ.get("ABA_BRAND_MONOGRAM", monogram)
    return name, tagline, monogram

BRAND_NAME, BRAND_TAGLINE, BRAND_MONOGRAM = _load_brand()


# ── Locale (data-token layer; see _vocab.py). Resolution order:
#    env ABA_LOCALE  ->  config/instance.yaml [instance].locale  ->  'en'.
# 'en' serves the English demo; 'ru' reproduces the original engine behavior
# (the engine's internal comparisons stay English — the locale layer normalizes
# discrete statuses at the loader boundary and selects locale data-tokens for
# the keyword/label matchers).
def _load_locale():
    locale = 'en'
    cfg_path = os.path.abspath(os.path.join(_HERE, "..", "config", "instance.yaml"))
    try:
        import yaml  # optional
        with open(cfg_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        inst = (data.get("instance") or {})
        locale = inst.get("locale", locale)
    except Exception:
        pass
    locale = os.environ.get("ABA_LOCALE", locale)
    locale = (locale or 'en').strip().lower()
    if locale not in ('en', 'ru'):
        locale = 'en'
    return locale

LOCALE = _load_locale()
