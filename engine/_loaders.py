_LOG_SEEN = set()

"""_loaders.py — loading JSON reports from daemons + state/*.json adapters.

JSON-only data layer. Registries (calendar.json / ukep.json / request_log.json)
were RETIRED in the JSON-first refactor (2026-06-19): load_calendar / load_ukep /
load_requests / load_client_pending are gone; deadlines + awaiting are aggregated
from per-client state via _deadlines.py. Daemon reports live in journal/inbox/
(anomalies_<date>.json, mail_<date>.json, news_<date>.json, updates_<date>.json,
finkoper_state/latest/*.json).
Contains: _DAEMON_DIAG (module-level variable),
load_daemon_finkoper/anomalies/mail/news/updates, and the state/*.json loaders.
"""
import os, json
from datetime import datetime as _dt, date, timedelta
import _vocab

_DAEMON_DIAG = {}  # name → {'status': ok|empty_unexpected|missing|error, 'count': N, 'detail': str}

def _log_once(key, msg):
    if key in _LOG_SEEN:
        return
    _LOG_SEEN.add(key)
    print(msg)

def _set_diag(name, status, count=0, detail=''):
    _DAEMON_DIAG[name] = {'status': status, 'count': count, 'detail': detail}



# load_calendar / load_ukep / load_requests REMOVED (JSON-first refactor 2026-06-19).
# The consolidated calendar, UKEP registry and request log were retired as data
# sources. Deadlines + awaiting are now aggregated from per-client state via
# _deadlines.collect_deadlines / collect_awaiting. The finkoper JSON snapshot
# loader (load_daemon_finkoper) below is unaffected and stays.

def _match_client_id(name_to_id, raw_name):
    """Exact match by name_short. If none — None."""
    return name_to_id.get((raw_name or '').strip())

def load_daemon_finkoper(diary_dir, today=None):
    """Finkoper via JSON snapshot journal/finkoper_state/latest/{tasks,chats}.json.
    Categorizes open tasks: overdue (deadline<today), soon (≤3 days), unread (chats with unread messages).
    No files / no JSON → graceful: empty lists + log."""
    import generate
    clients = generate.clients
    TODAY = generate.TODAY
    if today is None:
        today = TODAY
    state_dir = os.path.join(os.path.dirname(diary_dir), 'finkoper_state', 'latest')
    tasks_path = os.path.join(state_dir, 'tasks.json')
    chats_path = os.path.join(state_dir, 'chats.json')
    out = {'overdue': [], 'soon': [], 'unread': []}

    id_to_name = {c['id']: c['name_short'] for c in clients}

    if not os.path.exists(tasks_path):
        _log_once(f"finkoper-missing-{today}", f"[load_daemon_finkoper] tasks.json for {today} missing — {tasks_path}")
        _set_diag("finkoper", "missing", 0, "tasks.json not found")
        return out
    try:
        with open(tasks_path, encoding='utf-8') as f:
            tasks = json.load(f)
    except Exception as e:
        _log_once(f"finkoper-err-{today}", f"[load_daemon_finkoper] tasks.json could not be parsed: {e}")
        _set_diag("finkoper", "error", 0, f"tasks.json: {e}")
        return out

    for t in tasks:
        if t.get('status') != 'open':
            continue
        if t.get('internal'):
            continue
        cid = t.get('client_id')
        name_short = id_to_name.get(cid) or t.get('client_name', '—')
        deadline_raw = t.get('deadline')
        if not deadline_raw:
            continue
        try:
            dl = _dt.strptime(deadline_raw, '%Y-%m-%d').date()
        except ValueError:
            continue
        fields = [f"#{t.get('id','')}",
                  t.get('title', '')[:60],
                  f"due {dl.strftime('%d.%m.%Y')}"]
        item = {'client': name_short, 'fields': fields, 'task_id': t.get('id'),
                'url': t.get('url'), 'deadline': dl}
        if dl < today:
            out['overdue'].append(item)
        elif (dl - today).days <= 3:
            out['soon'].append(item)

    if not os.path.exists(chats_path):
        return out
    try:
        with open(chats_path, encoding='utf-8') as f:
            chats = json.load(f)
    except Exception as e:
        _log_once(f"finkoper-chats-err-{today}", f"[load_daemon_finkoper] chats.json could not be parsed: {e}")
        return out

    for ch in chats:
        if (ch.get('unread_count') or 0) <= 0:
            continue
        chat_name = ch.get('name', '') or ''
        matched = None
        for c in clients:
            short = c['name_short']
            family = short.replace('SP ', '').split(' ')[0]
            if short in chat_name or family in chat_name:
                matched = short
                break
        if not matched:
            continue
        fields = [ch.get('last_message_author', '') or '—',
                  (ch.get('last_message_preview', '') or '')[:80]]
        out['unread'].append({'client': matched, 'fields': fields,
                              'chat_url': ch.get('url'),
                              'count': ch.get('unread_count', 0)})
    total = len(out['overdue']) + len(out['soon']) + len(out['unread'])
    _set_diag("finkoper", "ok", total, f"overdue={len(out['overdue'])}, soon={len(out['soon'])}, unread={len(out['unread'])}")
    return out

def load_daemon_anomalies(diary_dir, today=None):
    """Anomalies from JSON file anomalies_<YYYY-MM-DD>.json.

    Schema:
        {"items": [{"client","severity"(high|medium|low),"title","description",
                    "context","source","suggested_action","anomaly_id","lifecycle"}]}
        client=None → system-wide anomaly.
    Returns a hybrid (same contract as before):
        - 'list': list of full dicts;
        - 'high'/'medium'/'low': legacy for calculate_health (client + text).
    No file / broken JSON → graceful: all keys empty + _set_diag."""
    import generate
    TODAY = generate.TODAY
    if today is None:
        today = TODAY
    path = os.path.join(diary_dir, f'anomalies_{today.isoformat()}.json')
    empty = {'list': [], 'high': [], 'medium': [], 'low': []}
    if not os.path.exists(path):
        _log_once(f"anomalies-missing-{today}", f"[load_daemon_anomalies] file for {today} missing — {path}")
        _set_diag("anomalies", "missing", 0, "no file")
        return empty
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        _log_once(f"anomalies-err-{today}", f"[load_daemon_anomalies] could not be parsed: {e}")
        _set_diag("anomalies", "error", 0, str(e))
        return empty

    items = []
    for it in (data.get('items') or []):
        items.append({
            'client': it.get('client'),
            'severity': it.get('severity'),
            'title': it.get('title', ''),
            'description': it.get('description', ''),
            'context': it.get('context', ''),
            'source': it.get('source', ''),
            'suggested_action': it.get('suggested_action', ''),
            'anomaly_id': it.get('anomaly_id', ''),
            'lifecycle': it.get('lifecycle', ''),
        })

    # legacy structure for calculate_health/collect_urgent
    by_sev = {'high': [], 'medium': [], 'low': []}
    for it in items:
        sev = it.get('severity')
        if sev in by_sev and it.get('client'):
            by_sev[sev].append({'client': it['client'], 'text': it.get('title', '')})

    n = len(items)
    if n == 0:
        _set_diag("anomalies", "ok", 0, "0 anomalies")
    else:
        _set_diag("anomalies", "ok", n, f"high={len(by_sev['high'])}, medium={len(by_sev['medium'])}, low={len(by_sev['low'])}")
    return {'list': items, **by_sev}

def load_daemon_mail(diary_dir, today=None):
    """Mail from JSON file mail_<YYYY-MM-DD>.json.

    Schema:
        {"items": [{"severity"(high|medium|low),"from_name","from_email","subject",
                    "received_at","client","preview","attachments":[...] }]}
    Returns a hybrid (same contract):
        - 'list': full dicts;
        - 'urgent'/'regular': legacy for collect_urgent (client + text + from).
    No file / broken JSON → graceful: all keys empty + _set_diag."""
    import generate
    TODAY = generate.TODAY
    if today is None:
        today = TODAY
    path = os.path.join(diary_dir, f'mail_{today.isoformat()}.json')
    empty = {'list': [], 'urgent': [], 'regular': []}
    if not os.path.exists(path):
        _log_once(f"mail-missing-{today}", f"[load_daemon_mail] file for {today} missing — {path}")
        _set_diag("mail", "missing", 0, "no file")
        return empty
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        _log_once(f"mail-err-{today}", f"[load_daemon_mail] could not be parsed: {e}")
        _set_diag("mail", "error", 0, str(e))
        return empty

    items = []
    for it in (data.get('items') or []):
        items.append({
            'severity': it.get('severity'),
            'from_name': (it.get('from_name') or '').strip(),
            'from_email': (it.get('from_email') or '').strip(),
            'subject': (it.get('subject') or '').strip(),
            'received_at': (it.get('received_at') or '').strip(),
            'client': it.get('client'),
            'preview': it.get('preview', ''),
            'attachments': it.get('attachments') or [],
        })

    # legacy for collect_urgent
    urgent, regular = [], []
    for it in items:
        legacy_text = it.get('subject') or it.get('preview', '')[:80]
        legacy = {'client': it.get('client') or '',
                  'text': legacy_text,
                  'from': it.get('from_name', '')}
        if it['severity'] == 'high':
            urgent.append(legacy)
        else:
            regular.append(legacy)

    n = len(items)
    if n == 0:
        _set_diag("mail", "ok", 0, "0 emails")
    else:
        _set_diag("mail", "ok", n, f"urgent={len(urgent)}, regular={len(regular)}")
    return {'list': items, 'urgent': urgent, 'regular': regular}


def load_daemon_news(diary_dir, today=None):
    """News from JSON file news_<YYYY-MM-DD>.json.

    Schema:
        {"items": [{"severity"(high|medium|low),"title","source","body","url"}]}
    Returns {'list': [...], 'high': [], 'medium': [], 'low': []} — same contract.
    No file / broken JSON → graceful: all empty + _set_diag."""
    import generate
    TODAY = generate.TODAY
    if today is None:
        today = TODAY
    path = os.path.join(diary_dir, f'news_{today.isoformat()}.json')
    empty = {'list': [], 'high': [], 'medium': [], 'low': []}
    if not os.path.exists(path):
        _log_once(f"news-missing-{today}", f"[load_daemon_news] file for {today} missing — {path}")
        _set_diag("news", "missing", 0, "no file")
        return empty
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        _log_once(f"news-err-{today}", f"[load_daemon_news] could not be parsed: {e}")
        _set_diag("news", "error", 0, str(e))
        return empty

    items = []
    for it in (data.get('items') or []):
        items.append({
            'severity': it.get('severity'),
            'title': (it.get('title') or '').strip(),
            'source': (it.get('source') or '').strip(),
            'body': it.get('body', ''),
            'url': it.get('url', ''),
        })

    by_sev = {'high': [], 'medium': [], 'low': []}
    for it in items:
        sev = it.get('severity')
        if sev in by_sev:
            by_sev[sev].append({'title': it.get('title', ''), 'url': it.get('url', '')})

    n = len(items)
    if n == 0:
        _set_diag("news", "ok", 0, "0 news items")
    else:
        _set_diag("news", "ok", n, f"high={len(by_sev['high'])}, medium={len(by_sev['medium'])}, low={len(by_sev['low'])}")
    return {'list': items, **by_sev}


def load_daemon_updates(diary_dir, today=None):
    """Knowledge base updates from JSON file updates_<YYYY-MM-DD>.json.

    Schema:
        {"items": [{"category"(applied|needs_manual|conflict),"label","title","body"}]}
    Returns {'list': [...], 'applied': [], 'needs_manual': [], 'conflict': []}.
    No file / broken JSON → graceful + _set_diag."""
    import generate
    TODAY = generate.TODAY
    if today is None:
        today = TODAY
    path = os.path.join(diary_dir, f'updates_{today.isoformat()}.json')
    empty = {'list': [], 'applied': [], 'needs_manual': [], 'conflict': []}
    if not os.path.exists(path):
        _log_once(f"updates-missing-{today}", f"[load_daemon_updates] file for {today} missing — {path}")
        _set_diag("updates", "missing", 0, "no file")
        return empty
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        _log_once(f"updates-err-{today}", f"[load_daemon_updates] could not be parsed: {e}")
        _set_diag("updates", "error", 0, str(e))
        return empty

    items = []
    for it in (data.get('items') or []):
        items.append({
            'category': it.get('category'),
            'label': (it.get('label') or '').strip(),
            'title': (it.get('title') or '').strip(),
            'body': (it.get('body') or '').strip(),
        })

    by_cat = {'applied': [], 'needs_manual': [], 'conflict': []}
    for it in items:
        cat = it.get('category')
        if cat in by_cat:
            by_cat[cat].append({'label': it.get('label', ''),
                                'title': it.get('title', ''),
                                'body': it.get('body', '')})

    n = len(items)
    if n == 0:
        _set_diag("updates", "ok", 0, "0 items")
    else:
        _set_diag("updates", "ok", n, f"applied={len(by_cat['applied'])}, needs_manual={len(by_cat['needs_manual'])}, conflict={len(by_cat['conflict'])}")
    return {'list': items, **by_cat}




# load_client_pending REMOVED (JSON-first refactor 2026-06-19) — the request
# log registry was retired. Per-client "awaiting" rows are derived from state
# via _deadlines.collect_awaiting.


# ---------- state/*.json loaders (v2 architecture, 2026-05-25) ----------

def load_client_state_tasks(client_id):
    """Reads the client's state/tasks.json. None if the file is missing."""
    try:
        from state_ops import state_read, state_exists
    except ImportError:
        return None
    if not state_exists(client_id, 'tasks.json'):
        return None
    data = state_read(client_id, 'tasks.json')
    return data if data else None


def state_tasks_to_mm_format(tasks_data, client_name=None):
    """Converts state/tasks.json into the mm-tracks format for the existing renderer.

    Args:
        tasks_data: dict from state/tasks.json
        client_name: explicit client name for each track (if None — try identity.json)
    """
    if not tasks_data or not tasks_data.get('tasks'):
        return {'tracks': []}
    if client_name is None:
        # try to pull from state/identity.json by client_id
        cid = tasks_data.get('client_id')
        if cid:
            ident = load_client_state_identity(cid)
            if ident:
                client_name = (ident.get('name') or {}).get('short')
    out = []
    for t in tasks_data['tasks']:
        out.append({
            'client_name': client_name,
            'client_id': tasks_data.get('client_id'),
            'id': t.get('id'),
            'title': t.get('title'),
            'status': t.get('status'),
            'type': t.get('task_type'),
            'created_at': t.get('created_at'),
            'due_date': t.get('due_date'),
            'amount': (t.get('type_specific') or {}).get('amount'),
            'anchors': t.get('labels', []),
            'context': t.get('context', ''),
            'next_action': t.get('next_action', ''),
            'reply_draft': '',
            'owner': t.get('assignee', ''),
            'source': t.get('source', ''),
            'anomaly_id': (t.get('linked') or {}).get('anomaly_id'),
            'last_event': None,
            'history': t.get('history', []),
            'linked': t.get('linked', {}) or {},
            'priority': t.get('priority', 'normal'),
            'blocked_by': t.get('blocked_by', []),
            'labels': t.get('labels', []),
            'comments': t.get('comments', []),
            'task_type': t.get('task_type'),
            'completed_at': t.get('completed_at'),
            'type_specific': t.get('type_specific', {}) or {},
        })
    return {'tracks': out}



def load_client_state_identity(client_id):
    """Reads the client's state/identity.json. None if the file is missing."""
    try:
        from state_ops import state_read, state_exists
    except ImportError:
        return None
    if not state_exists(client_id, 'identity.json'):
        return None
    data = state_read(client_id, 'identity.json')
    return data if data else None


def apply_identity_to_client(c, ident):
    """Enriches client record c with fields from state/identity.json.

    state/identity.json is the source of truth for details. clients_data.json
    remains as fallback/backup. Fields NOT in identity (banks, fresh_id,
    extras, monthly_check, etc.) are left untouched.

    Mutates c in place. Returns c for chainability.
    """
    if not ident:
        return c

    # Name
    name = ident.get('name') or {}
    if name.get('short'):
        c['name_short'] = name['short']
    if name.get('full'):
        c['name_full'] = name['full']
    if name.get('in_1c'):
        c['name_1c'] = name['in_1c']
    if name.get('uncertainty'):
        c['name_uncertainty'] = name['uncertainty']

    # Registration data
    for key in ('inn', 'ogrnip', 'reg_date', 'reg_started_year'):
        if ident.get(key) is not None:
            c[key] = ident[key]

    # Address
    addr = ident.get('addr') or {}
    if addr.get('city') or addr.get('full'):
        # Build a human-readable string for the existing renderer
        parts = []
        if addr.get('full'):
            parts.append(addr['full'])
        elif addr.get('city'):
            parts.append(addr['city'])
        if parts:
            c['addr'] = ', '.join(parts)
    if addr.get('region_pill'):
        c['pill_region'] = addr['region_pill']

    # IFNS
    ifns = ident.get('ifns') or {}
    if ifns.get('registration'):
        c['ifns'] = ifns['registration']
    if ifns.get('oktmo'):
        c['oktmo'] = ifns['oktmo']

    # OKVED
    okved = ident.get('okved') or {}
    main = okved.get('main') or {}
    if main.get('code'):
        c['okved'] = main['code']
    if main.get('name'):
        c['okved_name'] = main['name']
    additional = okved.get('additional') or []
    if additional:
        c['okved_additional'] = [item.get('code') for item in additional if item.get('code')]

    # Contacts
    contacts = ident.get('contacts') or {}
    for src, dst in (('phone', 'phone'), ('email', 'email')):
        if contacts.get(src):
            c[dst] = contacts[src]
    # Telegram/WhatsApp — for direct clients stored in messengers
    tg = contacts.get('telegram')
    wa = contacts.get('whatsapp')
    if tg or wa:
        msg = c.get('messengers') or {}
        if tg:
            msg['telegram'] = tg
        if wa:
            msg['whatsapp'] = wa
        c['messengers'] = msg

    return c



def load_client_state_regime(client_id):
    """Reads the client's state/regime.json. None if the file is missing."""
    try:
        from state_ops import state_read, state_exists
    except ImportError:
        return None
    if not state_exists(client_id, 'regime.json'):
        return None
    data = state_read(client_id, 'regime.json')
    return data if data else None


def apply_regime_to_client(c, regime):
    """Enriches the client with fields from state/regime.json.

    Main substitution: c['regime'] (string for the dashboard). Plus signature/filing/
    accounting_system/scenario/patents — for the renderers that support them.
    """
    if not regime:
        return c

    # Build the regime string for the existing renderer
    primary = regime.get('primary') or {}
    rtype = primary.get('type')
    obj = primary.get('object')
    rate = primary.get('rate')
    parts = []
    if rtype == 'USN':
        if obj == 'income':
            parts.append('USN Income')
        elif obj == 'income_minus_expense':
            parts.append('USN Income−Expenses')
        else:
            parts.append('USN')
        if rate is not None:
            parts.append(str(rate) + '%')
    elif rtype == 'AUSN':
        parts.append('AUSN')
        if obj == 'income':
            parts.append('Income')
        if rate is not None:
            parts.append(str(rate) + '%')
    elif rtype == 'OSNO':
        parts.append('OSNO')
    else:
        parts.append(rtype or '')

    # If there are active patents — add "+PSN"
    patents = regime.get('patents') or []
    if any(p.get('status') == 'active' for p in patents):
        parts.append('+ PSN')

    if parts:
        c['regime'] = ' '.join(parts).strip()

    # patent_active boolean
    c['patent_active'] = bool(any(p.get('status') == 'active' for p in patents))

    # scenario (for direct clients)
    if regime.get('scenario'):
        c['scenario'] = regime['scenario']
    if regime.get('scenario_name'):
        c['scenario_name'] = regime['scenario_name']

    # filing_method — merge with existing (if present in c)
    filing_in = regime.get('filing') or {}
    sig_in = regime.get('signature') or {}
    if filing_in or sig_in:
        fm = c.get('filing_method') or {}
        if filing_in.get('software') is not None:
            fm['decl_software'] = filing_in['software']
        if filing_in.get('submission_method') is not None:
            fm['submission'] = filing_in['submission_method']
        if sig_in.get('holder') is not None:
            fm['signature_holder'] = sig_in['holder']
        c['filing_method'] = fm

    # accounting_system
    if regime.get('accounting_system') is not None:
        c['accounting_system'] = regime['accounting_system']

    # patents — keep the structure for future renderers (the client, the client, etc.)
    if patents:
        c['patents'] = patents

    return c



def load_client_state_accounts(client_id):
    """Reads the client's state/accounts.json. None if the file is missing."""
    try:
        from state_ops import state_read, state_exists
    except ImportError:
        return None
    if not state_exists(client_id, 'accounts.json'):
        return None
    data = state_read(client_id, 'accounts.json')
    return data if data else None


def get_access(client_id, service=None):
    """🔗 Resolver for quick-access entries from accounts.quick_access[].

    service=None -> list of all entries;
    service in {finkoper, onec, bank, fns, prodamus, cloudpayments, ukassa, ofd} -> first entry or None.
    Each entry: {service,label,url,login,password,note,...}.
    Use at the start of a client task: take the link/access to a service from here
    rather than searching again (Finkoper card, bank portal, FNS portal, 1C base, Prodamus page).
    """
    acc = load_client_state_accounts(client_id)
    items = (acc or {}).get('quick_access') or []
    if service is None:
        return items
    for _it in items:
        if _it.get('service') == service:
            return _it
    return None


def apply_accounts_to_client(c, accounts):
    """Enriches the client with fields from state/accounts.json.

    The primary bank_account → substitutes c['bank_name']/['bik']/['account'].
    If there are foreign_accounts → substitutes c['foreign_accounts'] for the existing renderer.
    kassas — for the renderers that support them (the client).
    """
    if not accounts:
        return c

    # Primary bank account — real schema (Phase 2 fix 2026-05-25):
    # bank_accounts[i] has fields is_primary (bool), bank_name/bik/account at the top level,
    # closed_at (if None — the account is active). Previously apply looked for id='primary'/status='active'/bank.name —
    # those keys do not exist in the real schema, so apply silently failed to find the primary
    # and c['account']/['bank_name']/['bik'] stayed from the clients_data fallback.
    bas = accounts.get('bank_accounts') or []
    primary = None
    # 1) Take is_primary=True and not closed
    for ba in bas:
        if ba.get('is_primary') and not ba.get('closed_at'):
            primary = ba
            break
    # 2) Fallback: first not closed
    if primary is None:
        for ba in bas:
            if not ba.get('closed_at'):
                primary = ba
                break
    # 3) Last-resort fallback: just the first
    if primary is None and bas:
        primary = bas[0]
    if primary:
        if primary.get('bank_name'):
            c['bank_name'] = primary['bank_name']
        if primary.get('bik'):
            c['bik'] = primary['bik']
        if primary.get('account'):
            c['account'] = primary['account']

    # All accounts — as a separate field for future renderers (multi-account view)
    if bas:
        c['bank_accounts_all'] = bas

    # Foreign accounts (the client, the client)
    fas = accounts.get('foreign_accounts') or []
    if fas:
        c['foreign_accounts'] = fas

    # Cash registers
    kk = accounts.get('kassas') or []
    if kk:
        c['kassas'] = kk

    # bank_access merge (direct clients)
    bacc_in = accounts.get('bank_access') or {}
    if bacc_in:
        existing = c.get('bank_access') or {}
        # state is the source of truth, overwrite fields
        for k, v in bacc_in.items():
            if v is not None or k not in existing:
                existing[k] = v
        c['bank_access'] = existing

    return c



def load_client_state_financials(client_id):
    """Reads the client's state/financials.json. None if the file is missing."""
    try:
        from state_ops import state_read, state_exists
    except ImportError:
        return None
    if not state_exists(client_id, 'financials.json'):
        return None
    data = state_read(client_id, 'financials.json')
    return data if data else None


def apply_financials_to_client(c, fin):
    """Enriches the client with fields from state/financials.json.

    Puts structured periods/tax_calendar/yearly_pace into c['financials_v2'].
    The dashboard's Financial model & calendar section renders from this state
    (render_client_financials) — there is no Markdown source anymore.
    """
    if not fin:
        return c
    c['financials_v2'] = fin
    return c



def load_client_state_counterparties(client_id):
    """Reads the client's state/counterparties.json. None if the file is missing."""
    try:
        from state_ops import state_read, state_exists
    except ImportError:
        return None
    if not state_exists(client_id, 'counterparties.json'):
        return None
    data = state_read(client_id, 'counterparties.json')
    return data if data else None


def apply_counterparties_to_client(c, cp):
    """Enriches the client with fields from state/counterparties.json.

    Puts the list into c['counterparties_v2']; the dashboard's Counterparties
    section renders from this state. No Markdown source.
    """
    if not cp:
        return c
    cps = cp.get('counterparties') or []
    if cps:
        c['counterparties_v2'] = cps
    return c


def apply_risks_to_client(c, risks):
    """Enriches the client with fields from state/risks.json (Phase 2 of the CD migration, 2026-05-25).

    Puts risks.dismissed[] → c['dismissed_anomalies'] for backward compatibility
    with existing readers (_clients_group, _overview_v2, _aggregator).
    Also stores the full risks → c['risks_v2'] for new renderers.
    """
    if not risks:
        return c
    c['risks_v2'] = risks
    dismissed = risks.get('dismissed') or []
    if dismissed:
        c['dismissed_anomalies'] = dismissed
    return c


def apply_behavior_to_client(c, behavior):
    """Enriches the client with fields from state/behavior.json (Phase 2 of the CD migration, 2026-05-25).

    Mapping of old keys for backward compatibility:
      channels → c['messengers']  (read by _client_dashboard_v2, _analytics_widgets, etc.)
      special_notes → c['special_notes']  (read by card renderers)
      notes → c['extras']  (legacy key)
    """
    if not behavior:
        return c
    c['behavior_v2'] = behavior
    channels = behavior.get('channels')
    if channels:
        c['messengers'] = channels
    special = behavior.get('special_notes')
    if special:
        c['special_notes'] = special
    notes = behavior.get('notes')
    if notes is not None:
        c['extras'] = notes
    return c


def apply_tasks_overrides_to_client(c, tasks_data):
    """Enriches the client with tasks_overrides from state/tasks.json (Phase 2 of the CD migration, 2026-05-25).

    Puts tasks.tasks_overrides → c['tasks_overrides'] for backward compatibility
    with _helpers.py and _aggregator.py.
    """
    if not tasks_data:
        return c
    overrides = tasks_data.get('tasks_overrides')
    if overrides:
        c['tasks_overrides'] = overrides
    return c


def load_clients_from_index(index_path=None):
    """Phase 2 of the CD migration (2026-05-25): loads clients from clients_index.json
    and enriches them with fields from state/*.json via all apply_*_to_client functions.

    Returns list[dict] equivalent to the old clients[] format from clients_data.json.
    All fields (inn, regime, account, monthly_check, dismissed_anomalies, etc.) come
    from state — clients_data.json is no longer needed.

    Args:
        index_path: path to clients_index.json. None → default _data/clients_index.json.
    """
    import json
    if index_path is None:
        from _config import DATA_DIR
        index_path = os.path.join(DATA_DIR, 'clients_index.json')
    with open(index_path, encoding='utf-8') as f:
        index = json.load(f)

    clients = []
    for entry in index:
        # Base fields from the index
        c = dict(entry)
        cid = c['id']

        # Grouping field: `group` is canonical. Accept a legacy `track`
        # value (older index files) and normalize it to `group`.
        if 'group' not in c and 'track' in c:
            c['group'] = c.get('track')

        # Enrichment from state/*.json
        ident = load_client_state_identity(cid)
        if ident:
            apply_identity_to_client(c, ident)
        regime = load_client_state_regime(cid)
        if regime:
            apply_regime_to_client(c, regime)
        accounts = load_client_state_accounts(cid)
        if accounts:
            apply_accounts_to_client(c, accounts)
        fin = load_client_state_financials(cid)
        if fin:
            apply_financials_to_client(c, fin)
        cps = load_client_state_counterparties(cid)
        if cps:
            apply_counterparties_to_client(c, cps)
        risks = load_client_state_risks(cid)
        if risks:
            apply_risks_to_client(c, risks)
        behavior = load_client_state_behavior(cid)
        if behavior:
            apply_behavior_to_client(c, behavior)
        tasks_data = load_client_state_tasks(cid)
        if tasks_data:
            apply_tasks_overrides_to_client(c, tasks_data)

        clients.append(c)

    return clients



def build_snapshot_firm_from_state(client_id):
    """Builds the "Firmly known" facts (array of strings) from the client's state files.

    Returns list[str] for the snapshot's "Firmly understood" column. If no state
    file exists — returns None (the column then renders empty).

    Logic:
    - regime + business_description
    - counterparties — main (new = 🆕 if since is within the last 90 days)
    - financials — latest period + key taxes
    - tax_calendar — nearest unpaid payment
    - identity — details + OKVED + contacts
    """
    ident = load_client_state_identity(client_id)
    regime = load_client_state_regime(client_id)
    accounts = load_client_state_accounts(client_id)
    financials = load_client_state_financials(client_id)
    cps = load_client_state_counterparties(client_id)

    if not any([ident, regime, financials, cps]):
        return None

    facts = []
    from datetime import date, timedelta

    # 1. Regime + business
    if regime:
        primary = regime.get('primary') or {}
        scen = regime.get('scenario')
        scen_name = regime.get('scenario_name') or ''
        rtype = primary.get('type', '')
        obj = primary.get('object', '')
        rate = primary.get('rate')
        regime_str = ''
        if rtype == 'USN':
            obj_en = {'income': 'Income', 'income_minus_expense': 'Income−Expenses'}.get(obj, '')
            regime_str = 'USN ' + obj_en + (' ' + str(rate) + '%' if rate else '')
        elif rtype == 'AUSN':
            regime_str = 'AUSN'
        elif rtype:
            regime_str = rtype
        if scen:
            regime_str += ', scenario ' + str(scen)
            if scen_name:
                regime_str += ' — ' + scen_name
        if regime_str.strip():
            facts.append('**Regime:** ' + regime_str.strip())
        biz = regime.get('business_description')
        if biz:
            facts.append('**Business model:** ' + biz)

    # 2. Main counterparty (new if since is within the last 90 days)
    if cps:
        for cp in (cps.get('counterparties') or []):
            if cp.get('relation_type', '').startswith('b2b_customer_main'):
                name = cp.get('name', '')
                since = cp.get('since')
                category = cp.get('category', '')
                cat_en = {'gov_order': 'gov orders'}.get(category, category)
                tag = ''
                if since:
                    try:
                        sd = date.fromisoformat(since if len(since) == 10 else since + '-01')
                        if (date.today() - sd).days < 90:
                            tag = '🆕 '
                    except Exception:
                        pass
                line = tag + '**Main counterparty:** ' + name
                if cat_en:
                    line += ' — ' + cat_en
                facts.append(line)
                break

    # 3. Financials — latest period + next important payment
    if financials:
        periods = financials.get('periods') or []
        # archive = first, current = last
        if periods:
            cur = periods[-1]
            inc = cur.get('income_usn')
            per = cur.get('period', '')
            if inc is not None:
                inc_str = '{:,.2f}'.format(inc).replace(',', ' ').replace('.00', '')
                facts.append('**' + per + ':** income ' + inc_str + ' ₽')
            t = cur.get('taxes') or {}
            tax_bits = []
            if t.get('usn_advance') is not None and t.get('usn_advance_calculated'):
                tax_bits.append('USN advance ' + str(t['usn_advance']) +
                                ' (contributions ' + str(t.get('fixed_insurance_paid', 0)) +
                                ' covered ' + str(t['usn_advance_calculated']) + ')')
            elif t.get('usn_advance') is not None:
                tax_bits.append('USN advance ' + str(t['usn_advance']))
            if t.get('one_pct_overage'):
                tax_bits.append('1% surplus ' + str(t['one_pct_overage']))
            if tax_bits:
                facts.append('**Taxes ' + per + ':** ' + '; '.join(tax_bits))
        # nearest event from the calendar
        cal = financials.get('tax_calendar_2026') or []
        today_str = date.today().isoformat()
        upcoming = [x for x in cal if x.get('date', '') >= today_str and x.get('status') not in ('overlapped_by_insurance',)]
        if upcoming:
            upcoming.sort(key=lambda x: x.get('date', ''))
            n = upcoming[0]
            amt = n.get('amount') or n.get('amount_estimated')
            facts.append('**' + n.get('date', '') + ':** ' + n.get('what', '') +
                         (' — ' + str(amt) + ' ₽' if amt else ''))
        yp = financials.get('yearly_pace_2026') or {}
        if yp.get('growth_vs_prev_year_x'):
            facts.append('**Pace 2026:** ~' + str(yp.get('estimated_annual_income', '?')) +
                         ' annual (growth ' + str(yp['growth_vs_prev_year_x']) + 'x vs 2025)')

    # 4. Details + OKVED + contacts
    if ident:
        inn = ident.get('inn', '')
        ogrnip = ident.get('ogrnip', '')
        ifns = (ident.get('ifns') or {}).get('registration', '')
        bits = []
        if inn:
            bits.append('INN ' + inn)
        if ogrnip:
            bits.append('OGRNIP ' + ogrnip)
        if ifns:
            bits.append(ifns)
        if bits:
            facts.append('**Details:** ' + ', '.join(bits))
        okved = (ident.get('okved') or {}).get('main') or {}
        if okved.get('code'):
            line = '**OKVED:** ' + okved['code']
            if okved.get('name'):
                line += ' — ' + okved['name']
            add = ident.get('okved', {}).get('additional') or []
            if add:
                codes = [a.get('code') for a in add if a.get('code')]
                if codes:
                    line += ' (+' + str(len(codes)) + ' add\'l: ' + ', '.join(codes) + ')'
            facts.append(line)
        contacts = ident.get('contacts') or {}
        cbits = []
        if contacts.get('email'):
            cbits.append('Email ' + contacts['email'])
        if contacts.get('telegram'):
            cbits.append('TG ' + contacts['telegram'])
        if contacts.get('phone'):
            cbits.append('Tel ' + contacts['phone'])
        if cbits:
            facts.append('**Contacts:** ' + ', '.join(cbits))

    return facts



# Task statuses that count as "active / in flight" for the snapshot + tracks.
_ACTIVE_TASK_STATUSES = ('active', 'open', 'in_progress', 'awaiting', 'awaiting_external')


def build_snapshot_in_progress_from_state(client_id):
    """"In progress" snapshot column — derived from open/active tasks in state/tasks.json.

    Returns list[str] of task titles (active statuses only). None if there is no
    tasks.json at all (so the renderer can tell "no state" from "empty").
    """
    tasks_data = load_client_state_tasks(client_id)
    if tasks_data is None:
        return None
    items = []
    for t in (tasks_data.get('tasks') or []):
        if t.get('status') not in _ACTIVE_TASK_STATUSES:
            continue
        title = (t.get('title') or '').strip()
        if title:
            items.append(title)
    return items


def build_snapshot_unclear_from_state(client_id):
    """"Not yet clarified" snapshot column — derived from OPEN QUESTIONS / blockers in
    state/risks.json.

    Open questions are risks with kind=='question'; onboarding/operational blockers
    (kind=='blocker') are still unresolved unknowns, so they are included too.
    Resolved/green items are skipped. Returns list[str] of titles. None if no risks.json.
    """
    risks_data = load_client_state_risks(client_id)
    if risks_data is None:
        return None
    items = []
    for r in (risks_data.get('risks') or []):
        if r.get('severity') == 'green':
            continue
        if r.get('kind') in ('question', 'blocker'):
            title = (r.get('title') or '').strip()
            if title:
                items.append(title)
    return items


def build_history_from_state(client_id, limit=7):
    """Key-decisions history — derived from state/history.jsonl (newest first, top N).

    Each rendered line = '**<DD.MM.YYYY>** — <summary>' so the existing
    render_client_history (light **bold** markup) shows the date in bold.
    Returns list[str]. None if there is no history at all (graceful).
    """
    try:
        from state_ops import history_read
    except ImportError:
        return None
    entries = history_read(client_id)
    if not entries:
        return None

    def _fmt_ts(ts):
        s = str(ts or '')
        # ISO 'YYYY-MM-DD...' -> DD.MM.YYYY
        try:
            datepart = s.split('T')[0]
            y, m, d = datepart.split('-')[:3]
            return '{}.{}.{}'.format(d, m, y)
        except Exception:
            return s

    # newest first
    ordered = sorted(entries, key=lambda e: str(e.get('ts') or ''), reverse=True)
    out = []
    for e in ordered[:limit]:
        summary = (e.get('summary') or '').strip()
        if not summary:
            continue
        ts = _fmt_ts(e.get('ts'))
        out.append(('**' + ts + '** — ' if ts else '') + summary)
    return out


# ── v2 sections (financial model / tax calendar / work plan) FROM STATE ───────
# These build the same markdown shape the old mental_model v2 parser produced,
# so render_v2_block (_v2_sections) keeps working — but the source is JSON now.

def _fmt_money_v2(v):
    if v is None:
        return '—'
    try:
        return '{:,.2f}'.format(float(v)).replace(',', ' ').replace('.00', '')
    except Exception:
        return str(v)


_PERIOD_STATUS_EN = {
    'archive': 'archive', 'archive_micro': 'archive (micro)', 'calculated': 'calculated',
    'paid': 'paid', 'current': 'current', 'in_progress': 'in progress',
    'scheduled': 'scheduled', 'pending': 'pending',
}
_CAL_STATUS_EN = {
    'overlapped_by_insurance': 'offset by contributions', 'in_progress': 'in progress',
    'scheduled': 'scheduled', 'paid': 'paid', 'upcoming': 'upcoming', 'overdue': 'overdue',
    'sent': 'sent', 'done': 'done', 'pending': 'pending', 'decision_required': 'decision required',
}


def build_v2_sections_from_state(client_id):
    """Builds the v2 "Work plan" section as markdown from state/tasks.json.

    Only ``forward_plan`` is produced here. The financial model and tax calendar
    are deliberately left empty in this dict: they already have dedicated,
    state-driven renderers on the dashboard (render_client_financials reads the
    same state/financials.json), so duplicating them as v2 markdown tables would
    show two copies. red_flags / behavior_pattern / source_links / counterparties
    are likewise covered by their own state-driven sections (risks/behavior/
    counterparties), so they stay blank too. Returns a dict with all 7 v2 keys.
    """
    out = {
        'finmodel': '', 'tax_calendar': '', 'forward_plan': '',
        'red_flags': '', 'behavior_pattern': '', 'source_links': '', 'counterparties': '',
    }
    # --- Work plan (active tasks ahead) ---
    tasks_data = load_client_state_tasks(client_id)
    if tasks_data:
        active = [t for t in (tasks_data.get('tasks') or [])
                  if t.get('status') in _ACTIVE_TASK_STATUSES]
        if active:
            active.sort(key=lambda t: (t.get('due_date') or '9999'))
            plines = []
            for t in active:
                due = t.get('due_date') or ''
                due_s = (' (due ' + due + ')') if due else ''
                na = (t.get('next_action') or '').strip()
                na_s = (' — ' + na) if na else ''
                plines.append('- **' + (t.get('title') or '') + '**' + due_s + na_s)
            out['forward_plan'] = '\n'.join(plines)

    return out


def load_client_state_risks(client_id):
    """Reads the client's state/risks.json. None if the file is missing."""
    try:
        from state_ops import state_read, state_exists
    except ImportError:
        return None
    if not state_exists(client_id, 'risks.json'):
        return None
    data = state_read(client_id, 'risks.json')
    return data if data else None


def load_client_state_behavior(client_id):
    """Reads the client's state/behavior.json. None if the file is missing."""
    try:
        from state_ops import state_read, state_exists
    except ImportError:
        return None
    if not state_exists(client_id, 'behavior.json'):
        return None
    data = state_read(client_id, 'behavior.json')
    return data if data else None


# apply_risks_to_client / apply_behavior_to_client — now defined above
# (Phase 2 of the CD migration 2026-05-25, with backward compatibility for dismissed/messengers/special_notes/extras).
# The old minimal versions (only _v2) were removed to avoid redefinition.
