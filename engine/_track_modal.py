"""_track_modal.py — modal with the full track map (click on a track card).

v1.0 — modal with context and basic actions (Discuss/Dictate/Dashboard)
v1.1 — quick-actions (Done/Postpone/TG/Unclear)
v1.2 — breadcrumb on top (Dashboard › Client › Track), Dashboard button removed from footer

Created 2026-05-24.
"""

import json
from _strings import t
from _config import LOCALE


def _loc(en, ru):
    """Pick a localized literal for ru, else the English source."""
    return ru if LOCALE == 'ru' else en


# Russian labels for the "Details" (type_specific) rail. Injected into the modal
# JS as TS_RU_LOC (preferred over the English TS_RU map); empty under en.
_TS_RU_LOC = {
    "amount": "Сумма", "amount_estimated": "Сумма (оценка)", "kbk": "КБК",
    "payment_date": "Дата платежа", "payment_doc": "Платёжный документ", "payment_due": "Срок платежа",
    "paid_amount": "Оплачено (сумма)", "paid_at": "Оплачено", "awaiting_from": "Ждём от",
    "awaiting_for": "Ждём для", "awaiting_contact": "Ждём контакт", "awaiting_since": "Ждём с",
    "awaiting_expected_by": "Ожидается к", "expected_by": "Ожидается к",
    "expected_amount_estimate": "Ожидаемая сумма (оценка)", "silence_days": "Дней тишины",
    "overdue_days": "Дней просрочки", "since": "С", "channel": "Канал", "channels": "Каналы",
    "period": "Период", "file": "Файл", "files": "Файлы", "bank": "Банк", "contractor": "Контрагент",
    "counterparty_id": "Контрагент (ID)", "category": "Категория", "raised_at": "Заведено",
    "internal_deadline": "Внутренний дедлайн", "fns_deadline": "Дедлайн ФНС",
    "fns_notification_due": "Срок уведомления ФНС", "patent_period": "Период патента",
    "apply_date": "Дата подачи", "effective_from": "Действует с", "access": "Доступ",
    "breakdown": "Расшифровка", "cancel_reason": "Причина отмены", "cancelled_reason": "Причина отмены",
    "cancelled_at": "Отменено", "cancelled_note": "Примечание к отмене", "closed_reason": "Причина закрытия",
    "dismissed_reason": "Причина снятия", "reason_dropped": "Причина отклонения",
    "contract_via": "Договор через", "count": "Количество", "departed_at": "Ушёл",
    "departed_to": "Ушёл в", "dormant_during_pause": "Спит на паузе", "form": "Форма",
    "frequency": "Частота", "recurrence": "Повторяемость", "incident_date": "Дата инцидента",
    "invoice_number": "Номер счёта", "is_finalization": "Финализация", "items": "Позиции",
    "law_refs": "Ссылки на закон", "needed_for": "Нужно для", "promised_at": "Обещано",
    "promised_by": "Обещал", "reactivation_trigger": "Триггер реактивации", "receipt_npd": "Чек НПД",
    "replaced_by": "Заменено на", "request_sent_at": "Запрос отправлен", "resolution": "Решение",
    "resolved_at": "Решено", "responsibility": "Ответственность", "service": "Сервис",
    "sources": "Источники", "system": "Система", "sz_list": "Список самозанятых", "targets": "Цели",
    "tax_due_date": "Срок уплаты налога", "tax_paid_amount": "Налог уплачен (сумма)",
    "tax_paid_date": "Дата уплаты налога", "topic": "Тема", "topics": "Темы", "trigger": "Триггер",
    "verification_needed": "Требуется проверка", "uuid": "UUID",
    "remaining_operations": "Осталось операций", "account_id": "Счёт", "blocking_what": "Что блокирует",
    "dismissed_at": "Снято", "dismissed_by": "Снял", "dismissed_note": "Примечание к снятию",
    "finkoper_tasks": "Задачи Finkoper", "finkoper_task_url": "Ссылка на задачу",
    "change_date": "Дата изменения", "auditor": "Аудитор", "reminder_at": "Напоминание",
    "debit": "Дебет", "credit": "Кредит", "balance_end": "Исходящий остаток",
    "paid_outside_rs": "Оплачено вне счёта", "accounts_to_review": "Счета к проверке",
    "period_covered": "Покрытый период", "control_check_at": "Контрольная проверка",
    "status_detail": "Детализация статуса", "investigation_steps": "Шаги разбора",
    "memory_refs": "Ссылки на память", "check_cycles": "Циклы проверки", "loaded_until": "Загружено до",
    "balance_at_loaded": "Остаток на момент загрузки", "remaining_period": "Остаток периода",
    "kassas_ids": "Кассы", "owner_role": "Роль ответственного", "kkt_status": "Статус ККТ",
    "pending_corrections_amount": "Сумма к корректировке", "law_basis_penalty": "Норма (штраф)",
    "law_basis_escape": "Норма (освобождение)", "monitor_url": "Ссылка мониторинга",
    "target_regime": "Целевой режим", "okved": "ОКВЭД", "regions_candidate": "Регионы-кандидаты",
    "estimated_economy_per_year_rub": "Экономия в год, ₽",
    "psn_cost_spb_2026_per_vehicle_rub": "ПСН СПб 2026 за ТС, ₽",
    "spn_income_limit_2026_rub": "Лимит дохода 2026, ₽",
    "application_deadline_for_2026_07_01_start": "Срок подачи для старта с 01.07.2026",
    "application_form": "Форма заявления", "taxi_permit_law": "Закон о такси-разрешении",
    "pending_client_answers": "Ждём ответы клиента", "recommended_combo": "Рекомендуемая комбинация",
    "package_files_count": "Файлов в пакете", "contract": "Договор",
    "may_act_available_after": "Выписка за май доступна после",
    "requested_systems": "Запрошенные системы", "check_items": "Пункты проверки",
    "yearly_fixed": "Годовой фикс. взнос", "period_from": "Период с", "period_to": "Период по",
    "tax_amount_may_2026": "Налог за май 2026", "blocker_resolution": "Снятие блокера",
}


def _ts_ru_loc_json():
    return json.dumps(_TS_RU_LOC, ensure_ascii=False) if LOCALE == 'ru' else '{}'

TRACK_MODAL_CSS = """
.track-modal{position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:9999;
  display:none;align-items:center;justify-content:center;padding:var(--space-md)}
.track-modal.open{display:flex}
.track-modal-box{background:var(--bg-card);border-radius:var(--radius-card);
  max-width:860px;width:100%;max-height:90vh;overflow-y:auto;
  box-shadow:0 10px 40px rgba(0,0,0,0.2);padding:var(--space-lg);position:relative}

/* Two-column: solving content on the left, properties rail on the right (Linear) */
.tm-grid{display:grid;grid-template-columns:1fr 232px;gap:32px;align-items:start}
.tm-main{min-width:0}
.tm-aside{border-left:1px solid var(--border);padding-left:24px;min-width:0}
.tm-aside-h{font-size:11px;text-transform:uppercase;letter-spacing:.06em;
  color:var(--text-muted);font-weight:600;margin-bottom:12px}
.tm-aside .tm-meta-row{flex-direction:column;align-items:flex-start;gap:7px;
  margin:0;padding:0;border-bottom:none}
.tm-aside .tm-section{margin:16px 0 0}
.tm-aside .tm-section-label{font-size:11px;letter-spacing:.06em}
.tm-aside .tm-typespecific-grid{grid-template-columns:1fr;gap:2px}
.tm-aside .tm-typespecific-key{font-size:13px}
.tm-aside .tm-typespecific-val{font-size:14px;margin-bottom:6px}
@media (max-width:680px){
  .tm-grid{grid-template-columns:1fr;gap:0}
  .tm-aside{border-left:none;padding-left:0;margin-top:16px;
    border-top:1px solid var(--border);padding-top:16px}
  .tm-aside .tm-meta-row{flex-direction:row;flex-wrap:wrap}
}
.track-modal-close{position:absolute;top:var(--space-md);right:var(--space-md);
  background:none;border:none;font-size:20px;cursor:pointer;color:var(--text-muted);
  width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;z-index:2}
.track-modal-close:hover{background:var(--bg-page);color:var(--text-primary)}

/* Breadcrumb */
.tm-breadcrumb{display:flex;align-items:center;gap:4px;font-size:15px;
  color:var(--text-secondary);margin-bottom:var(--space-md);padding-right:40px;
  flex-wrap:wrap;line-height:1.5}
.tm-bc-link{color:var(--text-secondary);text-decoration:none;padding:3px 8px;
  border-radius:6px;transition:all 120ms;font-weight:500}
.tm-bc-link:hover{background:var(--bg-page);color:var(--accent-blue)}
.tm-bc-sep{color:var(--text-muted);font-size:14px;margin:0 2px;user-select:none}
.tm-bc-current{color:var(--text-primary);font-weight:500;padding:3px 8px}
.tm-bc-spacer{flex:1;min-width:8px}
/* Due now lives in the Properties rail — hide the duplicate breadcrumb badge */
.tm-bc-badge{display:none;font-size:15px;font-weight:500;padding:3px 10px;
  background:var(--red-bg);color:var(--accent-red);border-radius:8px;white-space:nowrap}
.tm-bc-badge.bc-yellow{background:var(--yellow-bg);color:var(--accent-yellow)}
.tm-bc-badge.bc-green{background:var(--green-bg);color:#3B5E2A}
.tm-bc-badge.bc-grey{background:var(--bg-page);color:var(--text-secondary)}

.tm-title{font-size:20px;font-weight:600;margin:0 0 14px;color:var(--text-primary);
  padding-right:40px;line-height:1.3;letter-spacing:-0.01em}
.tm-section{margin:16px 0;padding:0}
.tm-section-label{font-size:11px;color:var(--text-muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.06em;
  font-weight:600}
.tm-section-body{font-size:15px;line-height:1.6;color:var(--text-primary)}
/* Context reads as a lead paragraph, not a labeled form field */
#tm-context-section{margin-top:0}
#tm-context-section .tm-section-label{display:none}
#tm-context-body{font-size:16px;line-height:1.6;color:var(--text-primary)}
.tm-next-action{padding:12px 14px;background:var(--blue-bg);color:var(--text-primary);font-size:15px;line-height:1.55;border-radius:8px;border-left:3px solid var(--accent-blue)}
.tm-reply-draft{padding:var(--space-md) var(--space-lg);background:var(--green-bg);
  border-left:4px solid var(--accent-green);border-radius:0 var(--radius-btn) var(--radius-btn) 0;
  font-size:16px;line-height:1.7;color:var(--text-primary);white-space:pre-wrap}

.tm-actions{padding-top:18px;margin-top:20px;border-top:1px solid var(--border)}
.tm-actions-assist{display:flex;gap:10px;flex-wrap:wrap}
.tm-actions-assist:not(:empty){margin-bottom:12px}
.tm-actions-generic{display:flex;gap:10px;flex-wrap:wrap}
.tm-btn-sm{padding:7px 13px;font-size:14px;font-weight:500}
.tm-actions-secondary{margin-top:var(--space-sm);border-top:none;padding-top:0;
  display:flex;gap:8px;flex-wrap:wrap}
.tm-actions-secondary .tm-btn{font-size:15px;padding:8px 14px;opacity:0.9}
.tm-btn{padding:10px 16px;font-size:15px;border:1px solid var(--border);
  border-radius:var(--radius-btn);background:var(--bg-card);color:var(--text-primary);
  cursor:pointer;transition:all 150ms;text-decoration:none;display:inline-flex;
  align-items:center;gap:8px;font-family:inherit;font-weight:500}
.tm-btn:hover{border-color:var(--accent-blue);background:var(--blue-bg);color:var(--accent-blue)}
.tm-btn-primary{background:var(--accent-blue);color:#fff;border-color:var(--accent-blue)}
.tm-btn-primary:hover{background:#3a5c8f;color:#fff;border-color:#3a5c8f}
.tm-btn-success{background:var(--accent-green);color:#fff;border-color:var(--accent-green)}
.tm-btn-success:hover{background:#557546;color:#fff;border-color:#557546}
.tm-btn-warn{background:var(--accent-yellow);color:#fff;border-color:var(--accent-yellow)}
.tm-btn-warn:hover{background:#b8893a;color:#fff;border-color:#b8893a}
.tm-btn-tg{background:#2AABEE;color:#fff;border-color:#2AABEE}
.tm-btn-tg:hover{background:#1a8fc7;color:#fff;border-color:#1a8fc7}
.tm-meta-row{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 18px;padding-bottom:16px;border-bottom:1px solid var(--border)}
.tm-meta-chip{font-size:13px;padding:3px 9px;border-radius:6px;background:var(--bg-page);
  color:var(--text-primary);font-weight:500;border:1px solid var(--border)}
.tm-meta-chip.status-awaiting{background:var(--blue-bg);color:var(--accent-blue);border-color:transparent}
.tm-meta-chip.status-active{background:var(--green-bg);color:var(--accent-green);border-color:transparent}
.tm-meta-chip.status-blocked{background:var(--yellow-bg);color:var(--accent-yellow);border-color:transparent}
.tm-meta-chip.status-done{background:var(--bg-page);color:var(--text-muted);border-color:transparent}
.tm-meta-chip.prio-high{background:var(--red-bg);color:var(--accent-red);font-weight:500;border-color:transparent}
.tm-meta-chip.prio-low{background:var(--bg-page);color:var(--text-muted);border-color:transparent}
.tm-meta-chip.due-overdue{background:var(--red-bg);color:var(--accent-red);font-weight:500;border-color:transparent}
.tm-meta-chip.due-soon{background:var(--yellow-bg);color:#8A6730;border-color:transparent}
.tm-meta-chip.due-far{background:var(--bg-page);color:var(--text-secondary);border-color:transparent}
.tm-meta-chip.tm-stale{background:var(--yellow-bg);color:#8A6730;border-color:transparent;font-weight:600}

.tm-dep-link{display:block;padding:6px 10px;background:var(--yellow-bg);border-radius:4px;margin-bottom:4px;font-size:14px;color:#8A6730}
.tm-dep-link .dep-arrow{color:var(--text-muted);margin-right:6px}
.tm-dep-link .dep-id{font-size:14px;color:var(--text-muted);font-family:var(--font-mono,monospace);
  margin-left:8px}

.tm-typespecific-grid{display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;font-size:14px;
  line-height:1.6}
.tm-typespecific-key{color:var(--text-muted);font-weight:500}
.tm-typespecific-val{color:var(--text-primary)}
.tm-tscontent-item{margin-bottom:10px}
.tm-tscontent-k{font-size:12px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.03em;margin-bottom:2px}
.tm-tscontent-v{font-size:15px;line-height:1.55;color:var(--text-primary);white-space:pre-wrap}

.tm-labels{display:flex;flex-wrap:wrap;gap:6px}
.tm-label-chip{font-size:15px;padding:3px 10px;border-radius:12px;background:#EEEEEC;
  color:var(--text-secondary)}

.tm-comment{padding:10px 12px;background:var(--bg-page);border-radius:6px;margin-bottom:8px}
.tm-comment-meta{font-size:15px;color:var(--text-muted);margin-bottom:4px}
.tm-comment-text{font-size:14px;color:var(--text-primary);line-height:1.5}

.tm-history-list{display:flex;flex-direction:column;gap:0}
.tm-history-item{font-size:14px;line-height:1.55;padding:9px 0;border:none;border-bottom:1px solid var(--border);
  background:transparent;color:var(--text-secondary);border-radius:0}
.tm-history-item:last-child{border-bottom:none}
.tm-history-item .h-date{color:var(--text-muted);font-weight:500;font-family:var(--font-mono,monospace);
  font-size:13px;margin-right:9px}
.tm-history-item.auto{opacity:1}
.tm-history-item .h-src{display:inline-block;margin-left:8px;padding:2px 10px;border-radius:11px;font-size:13px;
  font-family:var(--font-mono,monospace);font-weight:700;background:var(--bg-page);color:var(--text-muted);border:1px solid var(--border)}
.tm-history-item .h-src-none{background:#F7D9D9;color:#8A1414;border:1px solid #E0A0A0}
.tm-history-item .h-auto{display:inline-block;margin-left:7px;padding:2px 9px;border-radius:11px;font-size:12px;
  font-weight:600;background:#E8E8E4;color:#444;border:1px solid #CFCFC8}
.tm-action-status{padding:var(--space-sm) var(--space-md);margin:var(--space-sm) 0;
  border-radius:var(--radius-btn);font-size:14px;display:none}
.tm-action-status.show{display:block}
.tm-action-status.success{background:var(--green-bg);color:#3B5E2A;border-left:3px solid var(--accent-green)}
.tm-action-status.error{background:var(--red-bg);color:var(--accent-red);border-left:3px solid var(--accent-red)}
.tm-action-status.info{background:var(--blue-bg);color:#0C447C;border-left:3px solid var(--accent-blue)}
.tm-assist-hyp{padding:11px 14px;background:var(--yellow-bg);border-left:3px solid var(--accent-yellow);border-radius:8px;font-size:15px;line-height:1.55;color:var(--text-primary);margin-bottom:12px}
.tm-assist-conf{font-size:13px;color:var(--text-muted);margin-left:6px}
.tm-assist-actions{display:flex;gap:8px;flex-wrap:wrap}
.tm-assist-btn{padding:9px 16px;font-size:15px;border:1px solid var(--border);border-radius:var(--radius-btn);background:var(--bg-card);color:var(--text-primary);cursor:pointer;font-family:inherit;font-weight:500;transition:all 150ms}
.tm-assist-btn:hover{border-color:var(--accent-blue);background:var(--blue-bg);color:var(--accent-blue)}
.tm-assist-btn.rec{border-color:var(--accent-blue);border-width:2px;padding:8px 15px}
.tm-assist-btn .rec-tag{font-size:12px;color:var(--accent-blue);margin-left:6px}
"""

# Static HTML template with __PLACEHOLDER__ tokens for the localizable chrome
# (headings, button labels, the Close title= attr). The tokens are substituted
# through t() below so the JS logic in TRACK_MODAL_JS is never touched.
_TRACK_MODAL_HTML_TEMPLATE = """
<div id="track-modal" class="track-modal">
  <div class="track-modal-box">
    <button class="track-modal-close" id="tm-close-btn" type="button" title="__CLOSE__">×</button>
    <div class="tm-breadcrumb">
      <a id="tm-bc-client" href="#" class="tm-bc-link">← <span id="tm-bc-client-name"></span></a>
      <span class="tm-bc-spacer"></span>
      <span id="tm-bc-badge" class="tm-bc-badge"></span>
    </div>
    <div class="tm-grid">
      <div class="tm-main">
        <h2 class="tm-title" id="tm-title"></h2>
        <div class="tm-section" id="tm-context-section" style="display:none">
          <div class="tm-section-label">__CONTEXT__</div>
          <div class="tm-section-body" id="tm-context-body"></div>
        </div>
        <div class="tm-section" id="tm-assist-section" style="display:none">
          <div class="tm-section-label">__HYPOTHESIS__</div>
          <div class="tm-assist-hyp" id="tm-assist-hyp"></div>
        </div>
        <div class="tm-section" id="tm-next-section" style="display:none">
          <div class="tm-section-label">__NEXT_ACTION__</div>
          <div class="tm-next-action" id="tm-next-body"></div>
        </div>
        <div class="tm-section" id="tm-tscontent-section" style="display:none">
          <div class="tm-section-label">__DETAILS_CONTENT__</div>
          <div class="tm-section-body" id="tm-tscontent-body"></div>
        </div>
        <div class="tm-section" id="tm-history-section" style="display:none">
          <div class="tm-section-label">__HISTORY__</div>
          <div class="tm-section-body tm-history-list" id="tm-history-body"></div>
        </div>
        <div class="tm-section" id="tm-comments-section" style="display:none">
          <div class="tm-section-label">__COMMENTS__</div>
          <div class="tm-section-body" id="tm-comments-body"></div>
        </div>
        <div class="tm-section" id="tm-reply-section" style="display:none">
          <div class="tm-section-label">__REPLY_DRAFT__</div>
          <div class="tm-reply-draft" id="tm-reply-body"></div>
        </div>
        <div class="tm-actions">
          <div class="tm-actions-assist" id="tm-assist-btns"></div>
          <div class="tm-actions-generic">
            <button class="tm-btn tm-btn-sm" id="tm-discuss-btn" type="button">__BREAK_DOWN__</button>
            <button class="tm-btn tm-btn-sm" id="tm-dictate-btn" type="button">__DICTATE__</button>
          </div>
        </div>
        <div class="tm-action-status" id="tm-action-status"></div>
      </div>
      <aside class="tm-aside">
        <div class="tm-aside-h">__PROPERTIES__</div>
        <div class="tm-meta-row" id="tm-meta-row" style="display:none"></div>
        <div class="tm-section" id="tm-typespecific-section" style="display:none">
          <div class="tm-section-label">__DETAILS__</div>
          <div class="tm-section-body" id="tm-typespecific-body"></div>
        </div>
        <div class="tm-section" id="tm-deps-section" style="display:none">
          <div class="tm-section-label">__DEPENDENCIES__</div>
          <div class="tm-section-body" id="tm-deps-body"></div>
        </div>
      </aside>
    </div>

  </div>
</div>
"""

TRACK_MODAL_HTML = (
    _TRACK_MODAL_HTML_TEMPLATE
    .replace('__CLOSE__', t('Close'))
    .replace('__CONTEXT__', t('📋 Context'))
    .replace('__HISTORY__', t('🕒 Event history'))
    .replace('__HYPOTHESIS__', t('🧭 System hypothesis'))
    .replace('__NEXT_ACTION__', t('🎯 Next action'))
    .replace('__DEPENDENCIES__', t('🔒 Dependencies'))
    .replace('__DETAILS__', t('📑 Details'))
    .replace('__DETAILS_CONTENT__', t('📋 Particulars'))
    .replace('__COMMENTS__', t('💬 Comments'))
    .replace('__REPLY_DRAFT__', t('💬 Draft reply to client'))
    .replace('__BREAK_DOWN__', t('🔍 Break down'))
    .replace('__DICTATE__', t('🎤 Dictate'))
    .replace('__PROPERTIES__', t('Properties'))
)

TRACK_MODAL_JS = r"""
<script>
(function(){
  var modal = document.getElementById('track-modal');
  var elBcClient = document.getElementById('tm-bc-client');
  var elBcBadge = document.getElementById('tm-bc-badge');
  var elTitle = document.getElementById('tm-title');
  var elCtxSec = document.getElementById('tm-context-section');
  var elCtxBody = document.getElementById('tm-context-body');
  var elNextSec = document.getElementById('tm-next-section');
  var elNextBody = document.getElementById('tm-next-body');
  var elReplySec = document.getElementById('tm-reply-section');
  var elReplyBody = document.getElementById('tm-reply-body');
  var elStatus = document.getElementById('tm-action-status');
  var btnDiscuss = document.getElementById('tm-discuss-btn');
  var btnDictate = document.getElementById('tm-dictate-btn');
  var btnClose = document.getElementById('tm-close-btn');
  var btnTg = null;  // tm-tg-btn removed

  var currentTrack = null;

  function shortTrackLabel(tid){
    if(!tid) return 'Track';
    // tr_client_i9_During formation... → i9
    var parts = tid.split('_');
    // look for the short ID (i9, t3, m1, etc.)
    for(var i = parts.length - 1; i >= 0; i--){
      var p = parts[i];
      if(/^[a-z]\d+$/i.test(p)) return 'Track ' + p;
    }
    // fallback — last segment
    var last = parts[parts.length - 1] || tid;
    return 'Track ' + last.slice(0, 20);
  }

  // Strip technical IDs out of human-readable text (context/history/hypothesis).
  // Related task titles are shown in the "Dependencies" block, so references
  // by short id ((i2)) and full ids (client_2026_2026_i2, tr_...) are cut out.
  function stripIds(s){
    if(!s) return s;
    s = String(s);
    s = s.replace(/blocked_by\s*=\s*[A-Za-z0-9_]+/g, '');
    s = s.replace(/\btr_[A-Za-z0-9_]+/g, '');
    s = s.replace(/\b[A-Za-z][A-Za-z0-9]*_\d{4}_\d{4}_[A-Za-z]\d+\b/g, '');
    // group of short ids joined by "+": i3+i7
    s = s.replace(/\b[a-z]\d+(?:\s*\+\s*[a-z]\d+)+\b/gi, '');
    // preposition + short id: "after i2", "before i2" → remove entirely (otherwise a dangling preposition is left)
    s = s.replace(/\s+(?:after|before|for|due to|because of|by|at|on|to)\s+[a-z]\d+\b/gi, '');
    // short id in parentheses: (i2)
    s = s.replace(/\s*\(\s*[a-z]\d+\s*\)/g, '');
    // standalone short id (i2, t3, m1 …)
    s = s.replace(/\b[a-z]\d+\b/g, '');
    // technical marker "Dedup …—" after end of sentence → remove, capitalize the next letter
    s = s.replace(/([.!?]\s*)[Dd]edup\w*\s*:?\s*[+\s]*[—–-]?\s*([a-z])/g, function(m, pre, ch){ return pre + ch.toUpperCase(); });
    // remaining "Dedup …—" anywhere
    s = s.replace(/[Dd]edup\w*\s*:?\s*[+\s]*[—–-]?\s*/g, '');
    s = s.replace(/\(\s*\)/g, '');
    s = s.replace(/\s{2,}/g, ' ');
    s = s.replace(/\s+([.,;:)])/g, '$1');
    s = s.replace(/[\s—–-]+$/, '');
    return s.trim();
  }

  function badgeClass(badge){
    if(!badge) return 'bc-grey';
    var b = String(badge).toLowerCase();
    if(b.indexOf('overdue') >= 0 || b === 'today') return '';
    if(b.indexOf('in 1d') >= 0 || b.indexOf('in 2d') >= 0 || b.indexOf('in 3d') >= 0) return 'bc-yellow';
    if(b.indexOf('in ') >= 0 || /\d{2}\.\d{2}/.test(b)) return 'bc-grey';
    if(b === 'awaiting' || b === 'waiting' || b.indexOf('waiting') >= 0) return 'bc-grey';
    return 'bc-grey';
  }

  function openTrackModal(card){
    currentTrack = {
      clientId: card.getAttribute('data-track-client-id') || '',
      clientName: card.getAttribute('data-track-client-name') || '',
      trackId: card.getAttribute('data-track-id') || '',
      title: card.getAttribute('data-track-title') || '',
      status: card.getAttribute('data-track-status') || '',
      badge: card.getAttribute('data-track-badge') || '',
      context: card.getAttribute('data-track-context') || '',
      nextAction: card.getAttribute('data-track-next') || '',
      replyDraft: card.getAttribute('data-track-reply') || '',
      tgUsername: card.getAttribute('data-track-tg') || '',
      taskType: card.getAttribute('data-track-task-type') || '',
      priority: card.getAttribute('data-track-priority') || 'normal',
      assignee: card.getAttribute('data-track-assignee') || '',
      due: card.getAttribute('data-track-due') || '',
      dueRaw: card.getAttribute('data-track-due-raw') || '',
      statusRaw: card.getAttribute('data-track-status-raw') || '',
      source: card.getAttribute('data-track-source') || '',
      blockedByJson: card.getAttribute('data-track-blocked-by-json') || '[]',
      labelsJson: card.getAttribute('data-track-labels-json') || '[]',
      typeSpecificJson: card.getAttribute('data-track-type-specific-json') || '{}',
      commentsJson: card.getAttribute('data-track-comments-json') || '[]',
      historyJson: card.getAttribute('data-track-history-json') || '[]',
      assistJson: card.getAttribute('data-track-assist-json') || '',
      stale: card.getAttribute('data-track-stale') || ''
    };
    // Breadcrumb: client link only (track's parent)
    var clientName = currentTrack.clientName;
    if(!clientName){
      // fallback: client name from the page h1
      var h1 = document.querySelector('.client-head h1');
      if(h1){
        var clone = h1.cloneNode(true);
        // strip child spans (h-dot, badge) — keep clean text
        Array.prototype.slice.call(clone.querySelectorAll('span.badge,span.h-dot')).forEach(function(n){ n.remove(); });
        clientName = clone.textContent.trim();
      }
    }
    var elBcClientName = document.getElementById('tm-bc-client-name');
    if(currentTrack.clientId && clientName){
      elBcClient.href = 'dashboard_' + currentTrack.clientId + '.html';
      if(elBcClientName) elBcClientName.textContent = clientName;
      elBcClient.style.display = '';
    } else {
      elBcClient.style.display = 'none';
    }
    if(currentTrack.badge && currentTrack.badge.toLowerCase() !== 'routine'){
      elBcBadge.textContent = currentTrack.badge;
      elBcBadge.className = 'tm-bc-badge ' + badgeClass(currentTrack.badge);
      elBcBadge.style.display = '';
    } else {
      elBcBadge.style.display = 'none';
    }
    elTitle.textContent = currentTrack.title;
    btnDiscuss.setAttribute('data-prompt', '__DISCUSS_PRE__' + (currentTrack.title || '') + '__DISCUSS_MID__' + (currentTrack.clientName || '') + '__DISCUSS_POST__');
    if(currentTrack.context){
      elCtxBody.textContent = stripIds(currentTrack.context);
      elCtxSec.style.display = '';
    } else { elCtxSec.style.display = 'none'; }
    if(currentTrack.nextAction){
      elNextBody.textContent = stripIds(currentTrack.nextAction);
      elNextSec.style.display = '';
    } else { elNextSec.style.display = 'none'; }
    if(currentTrack.replyDraft){
      elReplyBody.textContent = currentTrack.replyDraft;
      elReplySec.style.display = '';
    } else { elReplySec.style.display = 'none'; }
    // btnTg removed

    // === v2 rich render ===
    var esc = function(s){ return String(s||'').replace(/[&<>"]/g, function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); };

    // === assist: hypothesis (replaces "Next action") + actions in the footer ===
    var elAssistSec = document.getElementById('tm-assist-section');
    var elAssistHyp = document.getElementById('tm-assist-hyp');
    var elAssistBtns = document.getElementById('tm-assist-btns');
    var _assist = null;
    try { _assist = currentTrack.assistJson ? JSON.parse(currentTrack.assistJson) : null; } catch(e){ _assist = null; }
    if(elAssistBtns) elAssistBtns.innerHTML = '';
    if(_assist && _assist.hypothesis){
      var _conf = '';
      if(_assist.confidence || _assist.updated_at){
        _conf = '<span class="tm-assist-conf">(' + esc([_assist.confidence, _assist.updated_at].filter(Boolean).join(' · ')) + ')</span>';
      }
      elAssistHyp.innerHTML = esc(stripIds(_assist.hypothesis)) + _conf;
      if(elAssistSec) elAssistSec.style.display = '';
      if(elNextSec) elNextSec.style.display = 'none';
    } else if(elAssistSec){ elAssistSec.style.display = 'none'; }
    var _hasAssistActions = !!(_assist && _assist.actions && _assist.actions.length && elAssistBtns);
    if(_hasAssistActions){
      var _attr = function(s){ return String(s||'').replace(/[&<>"]/g, function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); };
      elAssistBtns.innerHTML = _assist.actions.map(function(a, i){
        return '<button class="tm-btn' + (a.recommended ? ' tm-btn-primary' : '') + '" data-prompt="' + _attr(a.prompt || '') + '">' + esc(stripIds(a.label || '') || ('__ACTION__ ' + (i+1))) + '</button>';
      }).join('');
    }
    // Always present one primary CTA. With an assist block, the recommended
    // action is primary. Without one, "Break down" is the default action.
    var _discussBtn = document.getElementById('tm-discuss-btn');
    if(_discussBtn){
      if(_hasAssistActions){ _discussBtn.classList.remove('tm-btn-primary'); }
      else { _discussBtn.classList.add('tm-btn-primary'); }
    }

    // Meta-row: status, priority, type, due, assignee, source
    var metaChips = [];
    if(currentTrack.statusRaw){
      var statusRu = {
        active: '__ST_ACTIVE__', awaiting: '__ST_WAITING__', awaiting_external: '__ST_WAITING_EXT__',
        blocked: '__ST_BLOCKED__', done: '__ST_CLOSED__', cancelled: '__ST_CANCELLED__'
      }[currentTrack.statusRaw] || currentTrack.statusRaw;
      var statusCls = 'status-' + currentTrack.statusRaw.replace('awaiting_external', 'awaiting');
      metaChips.push('<span class="tm-meta-chip ' + statusCls + '">●&nbsp;' + esc(statusRu) + '</span>');
    }
    if(currentTrack.priority && currentTrack.priority !== 'normal'){
      var prioRu = {high: '🔥 __PRIO_HIGH__', low: '__PRIO_LOW__'}[currentTrack.priority] || currentTrack.priority;
      metaChips.push('<span class="tm-meta-chip prio-' + currentTrack.priority + '">' + esc(prioRu) + '</span>');
    }
    if(currentTrack.stale){
      metaChips.push('<span class="tm-meta-chip tm-stale">\u23F3 __STALE_FOR__ ' + esc(currentTrack.stale) + ' __D_UNIT__</span>');
    }
    if(currentTrack.taskType && currentTrack.taskType !== '·'){
      metaChips.push('<span class="tm-meta-chip">' + esc(currentTrack.taskType) + '</span>');
    }
    if(currentTrack.due){
      var dueCls = 'due-far';
      if(currentTrack.due.indexOf('overdue') >= 0) dueCls = 'due-overdue';
      else if(currentTrack.due.indexOf('today') >= 0 || currentTrack.due.indexOf('tomorrow') >= 0) dueCls = 'due-soon';
      else if(currentTrack.due.match(/in [123]d/)) dueCls = 'due-soon';
      metaChips.push('<span class="tm-meta-chip ' + dueCls + '">📅 ' + esc(currentTrack.due) + '</span>');
    }
    if(currentTrack.assignee){
      metaChips.push('<span class="tm-meta-chip">👤 ' + esc(currentTrack.assignee) + '</span>');
    }
    var elMetaRow = document.getElementById('tm-meta-row');
    if(metaChips.length){
      elMetaRow.innerHTML = metaChips.join('');
      elMetaRow.style.display = '';
    } else { elMetaRow.style.display = 'none'; }

    // Dependencies (blocked_by with titles)
    var elDepsSec = document.getElementById('tm-deps-section');
    var elDepsBody = document.getElementById('tm-deps-body');
    try {
      var bb = JSON.parse(currentTrack.blockedByJson);
      if(bb && bb.length){
        elDepsBody.innerHTML = bb.map(function(d){
          var dt = d.title || '';
          if(!dt || dt === d.id) dt = '__RELATED_TASK__';
          return '<div class="tm-dep-link">' +
            '<span class="dep-arrow">→</span>' + esc(dt) +
          '</div>';
        }).join('');
        elDepsSec.style.display = '';
      } else { elDepsSec.style.display = 'none'; }
    } catch(e) { elDepsSec.style.display = 'none'; }

    // Type-specific details
    var elTsSec = document.getElementById('tm-typespecific-section');
    var elTsBody = document.getElementById('tm-typespecific-body');
    try {
      var ts = JSON.parse(currentTrack.typeSpecificJson);
      var keys = Object.keys(ts || {});
      if(keys.length){
        var TS_RU = {
          amount: 'Amount', amount_estimated: 'Amount (estimate)', kbk: 'KBK',
          payment_date: 'Payment date', payment_doc: 'Payment document', payment_due: 'Payment due',
          paid_amount: 'Amount paid', paid_at: 'Paid',
          awaiting_from: 'Waiting from', awaiting_for: 'Waiting for', awaiting_contact: 'Waiting on contact',
          awaiting_since: 'Waiting since', awaiting_expected_by: 'Expected by',
          expected_by: 'Expected by', expected_amount_estimate: 'Expected amount (estimate)',
          silence_days: 'Days of silence', overdue_days: 'Days overdue',
          since: 'Since', channel: 'Channel', channels: 'Channels', period: 'Period',
          file: 'File', files: 'Files', bank: 'Bank', contractor: 'Counterparty',
          counterparty_id: 'Counterparty (ID)', category: 'Category', raised_at: 'Raised',
          internal_deadline: 'Internal deadline', fns_deadline: 'FNS deadline',
          fns_notification_due: 'FNS notification due', patent_period: 'Patent period',
          apply_date: 'Filing date', effective_from: 'Effective from', access: 'Access',
          breakdown: 'Breakdown', cancel_reason: 'Cancellation reason', cancelled_reason: 'Cancellation reason',
          cancelled_at: 'Cancelled', cancelled_note: 'Cancellation note',
          closed_reason: 'Reason closed', dismissed_reason: 'Reason dropped',
          reason_dropped: 'Reason declined', contract_via: 'Contract via', count: 'Count',
          departed_at: 'Left', departed_to: 'Left for', dormant_during_pause: 'Dormant during pause',
          form: 'Form', frequency: 'Frequency', recurrence: 'Recurrence',
          incident_date: 'Incident date', invoice_number: 'Invoice number',
          is_finalization: 'Finalization', items: 'Items', law_refs: 'Law references',
          needed_for: 'Needed for', promised_at: 'Promised', promised_by: 'Promised by',
          reactivation_trigger: 'Reactivation trigger', receipt_npd: 'NPD receipt',
          replaced_by: 'Replaced by', request_sent_at: 'Request sent',
          resolution: 'Resolution', resolved_at: 'Resolved', responsibility: 'Responsibility',
          service: 'Service', sources: 'Sources', system: 'System', sz_list: 'SZ list',
          targets: 'Targets', tax_due_date: 'Tax due date', tax_paid_amount: 'Tax paid (amount)',
          tax_paid_date: 'Tax payment date', topic: 'Topic', topics: 'Topics',
          trigger: 'Trigger', verification_needed: 'Verification needed', uuid: 'UUID',
          remaining_operations: 'Operations remaining', account_id: 'Account', blocking_what: 'Blocking what', dismissed_at: 'Dropped', dismissed_by: 'Dropped by', dismissed_note: 'Drop note', finkoper_tasks: 'Finkoper tasks', finkoper_task_url: 'Task link', change_date: 'Change date', auditor: 'Auditor', reminder_at: 'Reminder', debit: 'Debit', credit: 'Credit', balance_end: 'Closing balance', paid_outside_rs: 'Paid outside account', accounts_to_review: 'Accounts to review', period_covered: 'Period covered', control_check_at: 'Control check', status_detail: 'Status detail', investigation_steps: 'Investigation steps', memory_refs: 'Memory references', check_cycles: 'Check cycles', loaded_until: 'Loaded until', balance_at_loaded: 'Balance at load', remaining_period: 'Remaining period', kassas_ids: 'Cash registers', owner_role: 'Assignee role', kkt_status: 'Cash register status', pending_corrections_amount: 'Amount to correct', law_basis_penalty: 'Statute (penalty)', law_basis_escape: 'Statute (exemption)', monitor_url: 'Monitoring link', target_regime: 'Target regime', okved: 'OKVED', regions_candidate: 'Candidate regions', estimated_economy_per_year_rub: 'Yearly savings, ₽', psn_cost_spb_2026_per_vehicle_rub: 'SPb 2026 patent per vehicle, ₽', spn_income_limit_2026_rub: 'Income limit 2026, ₽', application_deadline_for_2026_07_01_start: 'Application deadline for 2026-07-01 start', application_form: 'Application form', taxi_permit_law: 'Taxi permit law', pending_client_answers: 'Awaiting client answers', recommended_combo: 'Recommended combination', package_files_count: 'Files in package', contract: 'Contract', may_act_available_after: 'May statement available after', requested_systems: 'Requested systems', check_items: 'Check items', yearly_fixed: 'Yearly fixed contribution', period_from: 'Period from', period_to: 'Period to', tax_amount_may_2026: 'Tax for May 2026', blocker_resolution: 'Blocker resolution'
        };
        var TS_RU_LOC = __TS_RU_LOC_JSON__;
        // Separate CONTENT (free-form text / lists) from PROPERTIES (short scalars).
        function _tsIsContent(v){
          if(Array.isArray(v)) return true;
          if(typeof v === 'string'){
            if(v.indexOf('\n') >= 0) return true;
            if(v.length > 55) return true;
            if((v.match(/,/g) || []).length >= 2) return true;
          }
          return false;
        }
        function _tsFmt(v){
          if(Array.isArray(v)) return v.join(', ');
          if(typeof v === 'number') return v.toLocaleString('ru-RU');
          return String(v);
        }
        var propRows = [], contentRows = [];
        keys.filter(function(k){return ts[k] !== null && ts[k] !== '';}).forEach(function(k){
          var label = TS_RU_LOC[k] || TS_RU[k] || k.replace(/_/g,' ');
          var val = ts[k];
          if(_tsIsContent(val)){
            contentRows.push('<div class="tm-tscontent-item"><div class="tm-tscontent-k">' + esc(label) + '</div>' +
                             '<div class="tm-tscontent-v">' + esc(_tsFmt(val)) + '</div></div>');
          } else {
            propRows.push('<div class="tm-typespecific-key">' + esc(label) + ':</div>' +
                          '<div class="tm-typespecific-val">' + esc(_tsFmt(val)) + '</div>');
          }
        });
        if(propRows.length){
          elTsBody.innerHTML = '<div class="tm-typespecific-grid">' + propRows.join('') + '</div>';
          elTsSec.style.display = '';
        } else { elTsSec.style.display = 'none'; }
        var elTcSec = document.getElementById('tm-tscontent-section');
        var elTcBody = document.getElementById('tm-tscontent-body');
        if(elTcSec && elTcBody){
          if(contentRows.length){ elTcBody.innerHTML = contentRows.join(''); elTcSec.style.display = ''; }
          else { elTcSec.style.display = 'none'; }
        }
      } else { elTsSec.style.display = 'none'; }
    } catch(e) { elTsSec.style.display = 'none'; }


    // Comments
    var elCmSec = document.getElementById('tm-comments-section');
    var elCmBody = document.getElementById('tm-comments-body');
    try {
      var cmts = JSON.parse(currentTrack.commentsJson);
      if(cmts && cmts.length){
        elCmBody.innerHTML = cmts.map(function(c){
          return '<div class="tm-comment">' +
            '<div class="tm-comment-meta">' + esc(c.author || '—') + ' · ' + esc(c.ts || '') + '</div>' +
            '<div class="tm-comment-text">' + esc(c.text || '') + '</div>' +
          '</div>';
        }).join('');
        elCmSec.style.display = '';
      } else { elCmSec.style.display = 'none'; }
    } catch(e) { elCmSec.style.display = 'none'; }

    // History
    var elHistSec = document.getElementById('tm-history-section');
    var elHistBody = document.getElementById('tm-history-body');
    try {
      var hist = JSON.parse(currentTrack.historyJson);
      var TECH = /resolves_when|no_auto_resolve|blocked_by|hardening|backfill|signal.?process/i;
      hist = (hist || []).filter(function(h){
        var t = (h.event || h.summary || '');
        return t && !TECH.test(t);
      });
      if(hist.length){
        elHistBody.innerHTML = hist.slice().reverse().map(function(h){
          var autoCls = h.auto ? ' auto' : '';
          var src = (h.source || '').trim();
          var srcHtml = src ? '<span class="h-src">' + esc(src) + '</span>' : '';
          var autoHtml = h.auto ? '<span class="h-auto">__AUTO__</span>' : '';
          return '<div class="tm-history-item' + autoCls + '">' +
            '<span class="h-date">' + esc(h.date || h.ts || '') + '</span>' +
            esc(stripIds(h.event || h.summary || '')) +
            srcHtml + autoHtml +
          '</div>';
        }).join('');
        elHistSec.style.display = '';
      } else { elHistSec.style.display = 'none'; }
    } catch(e) { elHistSec.style.display = 'none'; }

    elStatus.className = 'tm-action-status';
    elStatus.textContent = '';
    modal.classList.add('open');
  }

  function closeTrackModal(){ modal.classList.remove('open'); currentTrack = null; }

  function showStatus(text, kind){
    elStatus.textContent = text;
    elStatus.className = 'tm-action-status show ' + (kind || 'info');
  }

  function copyToClipboard(text){
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed'; ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.focus(); ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch(e) {}
    document.body.removeChild(ta);
    return ok;
  }

  btnClose.addEventListener('click', closeTrackModal);
  modal.addEventListener('click', function(e){ if(e.target === modal) closeTrackModal(); });
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape' && modal.classList.contains('open')) closeTrackModal();
  });

  btnDictate.addEventListener('click', function(){
    if(!currentTrack) return;
    if(typeof window.openMicModal === 'function'){
      window.openMicModal({
        kind: 'track',
        id: currentTrack.trackId,
        client: currentTrack.clientName,
        title: currentTrack.title,
        extra: currentTrack.badge || currentTrack.status
      });
    } else {
      console.warn('window.openMicModal not available');
    }
  });

  document.addEventListener('click', function(e){
    var inner = e.target.closest('button,a');
    if(inner) return;
    var card = e.target.closest('.track-card-clickable[data-track-id]');
    if(card){ e.preventDefault(); openTrackModal(card); }
  });
})();
</script>
"""

# Localize the JS-side chrome literals (status / priority / stale / related-task /
# action / auto). These render at runtime inside the modal, so they live as
# __TOKEN__ placeholders in the script and are substituted through t() here —
# the same pattern as the static HTML template above. JS logic is untouched.
TRACK_MODAL_JS = (
    TRACK_MODAL_JS
    .replace('__ST_ACTIVE__', t('active'))
    .replace('__ST_WAITING_EXT__', t('waiting (external)'))
    .replace('__ST_WAITING__', t('waiting'))
    .replace('__ST_BLOCKED__', t('blocked'))
    .replace('__ST_CLOSED__', t('closed'))
    .replace('__ST_CANCELLED__', t('cancelled'))
    .replace('__PRIO_HIGH__', t('high priority'))
    .replace('__PRIO_LOW__', t('low priority'))
    .replace('__STALE_FOR__', t('stale for'))
    .replace('__D_UNIT__', t('d'))
    .replace('__RELATED_TASK__', t('Related task'))
    .replace('__ACTION__', t('Action'))
    .replace('__AUTO__', t('auto'))
    .replace('__TS_RU_LOC_JSON__', _ts_ru_loc_json())
    .replace('__DISCUSS_PRE__', _loc('Break down the task "', 'Разбери задачу «'))
    .replace('__DISCUSS_MID__', _loc('" for client ', '» для клиента '))
    .replace('__DISCUSS_POST__', _loc(
        '. Open the client state/*.json (source of truth) and mental_model (narrative), '
        'check related sources (Telegram/email/Finkoper) and reconcile the links. '
        'First update the model with the new signal, then suggest a concrete next action. '
        'Make any state change via mm_update (with my approval); send nothing outward without my OK.',
        '. Открой state/*.json клиента (источник истины) и mental_model (нарратив), '
        'проверь связанные источники (Telegram/почта/Finkoper) и сверь связи. '
        'Сначала обнови модель новым сигналом, затем предложи конкретное следующее действие. '
        'Правки state — через mm_update (с моим аппрувом); наружу ничего не отправляй без моего «ок».'))
)
