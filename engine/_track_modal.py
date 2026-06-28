"""_track_modal.py — modal with the full track map (click on a track card).

v1.0 — modal with context and basic actions (Discuss/Dictate/Dashboard)
v1.1 — quick-actions (Done/Postpone/TG/Unclear)
v1.2 — breadcrumb on top (Dashboard › Client › Track), Dashboard button removed from footer

Created 2026-05-24.
"""

import json
from _strings import t
from _config import LOCALE
from _helpers import _SRC_LABELS, _SRC_GENERIC


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
    "doc_expected": "Ожидаемый документ", "deadline": "Срок", "decision": "Решение",
    "next_step": "Следующий шаг", "amount_paid": "Оплачено (сумма)", "payment_basis": "Основание платежа",
    "service_quarter": "Квартал обслуживания", "tariff_note": "Тариф (примечание)",
    "wake_date": "Возобновить (дата)", "wake_to": "Спит до", "jur_services": "Юр. услуги",
    "condition": "Условие", "contract_termination_date": "Дата расторжения договора",
    "activation": "Активация", "advance_calc_gross": "Расчёт аванса (брутто)",
    "advance_due_q1": "Аванс за 1 кв (срок)", "filled_through": "Заполнено по",
    "form_when": "Когда формировать", "last_verified_period": "Последний проверенный период",
    "legal_basis": "Правовое основание", "payer": "Плательщик", "payment_tranches": "Транши платежа",
    "reconciliation_status": "Статус сверки", "review_date": "Дата проверки",
    "threshold_law": "Норма о пороге", "q1_2026_paid": "Оплачено за 1 кв 2026",
    "q4_2025_paid": "Оплачено за 4 кв 2025",
}


def _ts_ru_loc_json():
    return json.dumps(_TS_RU_LOC, ensure_ascii=False) if LOCALE == 'ru' else '{}'

# type_specific keys the generic Details rail skips — internal plumbing, or rendered
# by a dedicated modal section (payroll_lines/totals).
INTERNAL_TS_KEYS = ['no_auto_resolve', 'id_slug_note', 'exclude', 'feeds',
                    'resolved_value', 'resolves_when',
                    # the entity-linking reference list (structural, read by derivations):
                    'refs',
                    # rendered by a DEDICATED modal section, not the generic KV rail:
                    'payroll_lines', 'totals', 'review', '_summary']

def _ts_internal_json():
    return json.dumps(INTERNAL_TS_KEYS)

def _pay_l10n_json():
    # Locale-correct labels for the payroll-run table (injected like TS_RU_LOC).
    return json.dumps({
        'emp': t('Employee'), 'gross': t('Gross'), 'net': t('Net'),
        'check': t('Check'), 'total': t('Total'), 'reconciled': t('reconciled'),
        'review': t('to review'), 'mismatch': t('mismatch'), 'allOk': t('all reconciled'),
        'newL': t('new'), 'thr': t('incl. THR'), 'lines': t('lines'), 'changes': t('changes'),
        'okL': t('parity-ok'), 'socgap': t('social-gap'),
    }, ensure_ascii=False)

TRACK_MODAL_CSS = """
.tm-pay-table{width:100%;border-collapse:collapse;font-size:14px;margin-top:4px}
.tm-pay-table th{text-align:left;color:var(--muted,#6b7280);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.4px;padding:7px 9px;border-bottom:1px solid var(--line,#e8eaf0)}
.tm-pay-table th.num,.tm-pay-table td.num{text-align:right;font-variant-numeric:tabular-nums}
.tm-pay-table td{padding:9px 9px;border-bottom:1px solid var(--line,#e8eaf0)}
.tm-pay-table tbody tr.warn td:first-child{box-shadow:inset 3px 0 0 var(--accent-yellow)}
.tm-pay-pill{font-size:11.5px;padding:2px 8px;border-radius:9px;white-space:nowrap}
.tm-pay-ok{background:var(--green-bg);color:var(--accent-green)}
.tm-pay-bad{background:var(--red-bg);color:var(--accent-red)}
.tm-pay-warn{background:var(--yellow-bg);color:var(--accent-yellow)}
.tm-pay-name{font-weight:600;font-size:14px}
.tm-pay-delta{font-size:12.5px;color:var(--muted,#8A909C);font-weight:500;margin-left:7px}
.tm-pay-kasrow{display:inline-flex;gap:10px;flex-wrap:wrap}
.tm-pay-kas{display:inline-flex;align-items:center;gap:5px;font-size:12.5px;color:var(--text-secondary,#565B66)}
.tm-pay-kas i{width:7px;height:7px;border-radius:50%;background:var(--accent-green,#3E8E5E)}
.tm-pay-kas.off{color:var(--muted,#8A909C)}
.tm-pay-kas.off i{background:var(--border-strong,#D8DCE2)}
.tm-band-gap{color:var(--accent-yellow,#A8782B);font-weight:600}
.tm-band-flag{display:inline-flex;align-items:center;gap:5px;color:var(--accent-red,#C24A3D);font-weight:600}
.tm-band-flag i{width:6px;height:6px;border-radius:50%;background:var(--accent-red,#C24A3D)}
.tm-pay-sub{font-size:12px;color:var(--muted,#6b7280);margin-top:2px;display:flex;align-items:center;gap:5px}
.tm-pay-tag{font-size:10.5px;padding:1px 6px;border-radius:8px;background:var(--accent-soft,#eef0fb);color:var(--accent-text,#1F4E79);margin-left:4px}
.tm-pay-foot td{font-weight:700;border-top:2px solid var(--line,#e8eaf0);border-bottom:0;font-variant-numeric:tabular-nums;font-size:14px}
.tm-pay-recon{font-size:13px;margin-top:8px}
.tm-pay-band{display:flex;flex-wrap:wrap;gap:7px;align-items:center;background:#fafbff;border:1px solid var(--line,#e8eaf0);border-radius:8px;padding:9px 12px;margin-bottom:11px;font-size:13px;color:var(--muted,#6b7280)}
.tm-band-i b{color:var(--accent-text,#1F4E79)}
.tm-band-sep{width:1px;height:14px;background:var(--line,#e8eaf0)}
.tm-pay-neutral{background:#eef0f3;color:var(--muted,#6b7280)}
.tm-pay-sub2{font-size:11.5px;color:var(--muted,#6b7280);margin-top:1px}
.track-modal{position:fixed;inset:0;background:rgba(18,18,28,0.34);z-index:9999;
  display:none;align-items:center;justify-content:center;padding:var(--space-lg);
  -webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px)}
.track-modal.open{display:flex;animation:tm-fade 140ms ease}
@keyframes tm-fade{from{opacity:0}to{opacity:1}}
.track-modal-box{background:var(--bg-card);border-radius:16px;border:1px solid var(--border);
  max-width:780px;width:100%;max-height:90vh;overflow-y:auto;
  box-shadow:0 24px 64px -16px rgba(16,16,26,0.30),0 4px 12px rgba(16,16,26,0.06);
  padding:38px 44px 0;position:relative;animation:tm-rise 160ms cubic-bezier(.2,.7,.3,1)}
/* payroll-run tracks carry a wide multi-column table — give the box room */
.track-modal-box.tm-wide{max-width:1040px}
@keyframes tm-rise{from{transform:translateY(8px);opacity:.6}to{transform:translateY(0);opacity:1}}

/* Two-column: solving content on the left, properties rail on the right (Linear) */
.tm-grid{display:block}
.tm-section.tm-section-secondary{margin:28px 0 0;padding-top:22px;border-top:1px solid var(--border)}
.tm-section.tm-section-secondary .tm-section-label{color:var(--text-muted);margin-bottom:14px}
.tm-main{min-width:0}
.tm-aside{border-left:1px solid var(--border);padding-left:32px;padding-bottom:30px;min-width:0}
.tm-aside-h{font-size:11px;text-transform:uppercase;letter-spacing:.08em;
  color:var(--text-muted);font-weight:600;margin-bottom:14px}
.tm-aside .tm-meta-row{flex-direction:column;align-items:flex-start;gap:8px;
  margin:0;padding:0;border-bottom:none}
.tm-aside .tm-section{margin:20px 0 0}
.tm-aside .tm-section-label{font-size:11px;letter-spacing:.08em}
.tm-aside .tm-typespecific-grid{grid-template-columns:1fr;gap:1px}
.tm-aside .tm-typespecific-key{font-size:12px;color:var(--text-muted);margin-bottom:1px}
.tm-aside .tm-typespecific-val{font-size:14px;margin-bottom:12px;color:var(--text-primary)}
@media (max-width:720px){
  .track-modal-box{padding:26px 22px 0}
  .tm-grid{grid-template-columns:1fr;gap:0}
  .tm-aside{border-left:none;padding-left:0;margin-top:20px;
    border-top:1px solid var(--border);padding-top:20px}
  .tm-aside .tm-meta-row{flex-direction:row;flex-wrap:wrap}
}
.track-modal-close{position:absolute;top:18px;right:18px;
  background:none;border:none;font-size:18px;cursor:pointer;color:var(--text-muted);
  width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;z-index:2;
  transition:all 120ms}
.track-modal-close:hover{background:var(--bg-page);color:var(--text-primary)}

/* Breadcrumb */
.tm-breadcrumb{display:flex;align-items:center;gap:4px;font-size:14px;
  color:var(--text-secondary);margin-bottom:18px;padding-right:40px;
  flex-wrap:wrap;line-height:1.5}
.tm-bc-link{color:var(--text-muted);text-decoration:none;padding:4px 10px 4px 0;
  border-radius:6px;transition:all 120ms;font-weight:500}
.tm-bc-link:hover{color:var(--accent)}
.tm-bc-sep{color:var(--text-muted);font-size:14px;margin:0 2px;user-select:none}
.tm-bc-current{color:var(--text-primary);font-weight:500;padding:3px 8px}
.tm-bc-spacer{flex:1;min-width:8px}
/* Due now lives in the Properties rail — hide the duplicate breadcrumb badge */
.tm-bc-badge{display:none;font-size:15px;font-weight:500;padding:3px 10px;
  background:var(--red-bg);color:var(--accent-red);border-radius:8px;white-space:nowrap}
.tm-bc-badge.bc-yellow{background:var(--yellow-bg);color:var(--accent-yellow)}
.tm-bc-badge.bc-green{background:var(--green-bg);color:#3B5E2A}
.tm-bc-badge.bc-grey{background:var(--bg-page);color:var(--text-secondary)}

.tm-title{font-size:23px;font-weight:600;margin:2px 0 14px;color:var(--text-primary);
  padding-right:40px;line-height:1.28;letter-spacing:-0.02em}
.tm-section{margin:22px 0;padding:0}
.tm-section-label{font-size:11px;color:var(--text-muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:.07em;
  font-weight:600}
.tm-section-body{font-size:15px;line-height:1.65;color:var(--text-primary)}
/* Context reads as a lead paragraph, not a labeled form field */
#tm-context-section{margin-top:0;margin-bottom:24px}
#tm-context-section .tm-section-label{display:none}
#tm-context-body{font-size:16.5px;line-height:1.65;color:var(--text-secondary);white-space:pre-wrap}
.tm-next-action{padding:13px 16px;background:var(--blue-bg);color:var(--text-primary);font-size:15px;line-height:1.55;border-radius:10px;border-left:3px solid var(--accent-blue);white-space:pre-wrap}
.tm-reply-draft{padding:var(--space-md) var(--space-lg);background:var(--green-bg);
  border-left:4px solid var(--accent-green);border-radius:0 var(--radius-btn) var(--radius-btn) 0;
  font-size:16px;line-height:1.7;color:var(--text-primary);white-space:pre-wrap}

/* Action bar pinned to the bottom of the scroll area so the primary CTA stays
   reachable on long tasks. Background masks content scrolling underneath. */
.tm-actions{position:sticky;bottom:0;z-index:3;margin-top:24px;padding:16px 0 26px;
  background:var(--bg-card);border-top:1px solid var(--border);
  display:flex;flex-wrap:wrap;gap:10px;align-items:center}
/* assist actions + the generic button share one wrapping row */
.tm-actions-assist,.tm-actions-generic{display:contents}
.tm-actions-secondary{margin-top:var(--space-sm);border-top:none;padding-top:0;
  display:flex;gap:8px;flex-wrap:wrap}
/* The button system itself (.tm-btn + size/colour modifiers) is defined ONCE
   in _css.py. Do not redefine it here — only modal-scoped tweaks belong below. */
.tm-actions-secondary .tm-btn{opacity:0.9}
.tm-meta-row{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 24px}
.tm-meta-chip{font-size:12.5px;padding:4px 11px;border-radius:7px;background:var(--bg-page);
  color:var(--text-secondary);font-weight:500;border:1px solid var(--border);
  display:inline-flex;align-items:center;gap:5px;line-height:1.3}
.tm-meta-chip.status-awaiting{background:var(--blue-bg);color:var(--accent-blue);border-color:transparent}
.tm-meta-chip.status-active{background:var(--green-bg);color:var(--accent-green);border-color:transparent}
.tm-meta-chip.status-blocked{background:var(--yellow-bg);color:var(--accent-yellow);border-color:transparent}
.tm-meta-chip.status-done{background:var(--bg-page);color:var(--text-muted);border-color:transparent}
.tm-meta-chip.status-in_progress,.tm-meta-chip.status-paid{background:var(--green-bg);color:var(--accent-green);border-color:transparent}
.tm-meta-chip.status-scheduled,.tm-meta-chip.status-calculated{background:var(--blue-bg);color:var(--accent-blue);border-color:transparent}
.tm-meta-chip.status-deferred,.tm-meta-chip.status-dropped,.tm-meta-chip.status-cancelled,.tm-meta-chip.status-archived{background:var(--bg-page);color:var(--text-muted);border-color:transparent}
.tm-meta-chip.prio-high{background:var(--red-bg);color:var(--accent-red);font-weight:500;border-color:transparent}
.tm-meta-chip.prio-low{background:var(--bg-page);color:var(--text-muted);border-color:transparent}
.tm-meta-chip.due-overdue{background:var(--red-bg);color:var(--accent-red);font-weight:500;border-color:transparent}
.tm-meta-chip.due-soon{background:var(--yellow-bg);color:#8A6730;border-color:transparent}
.tm-meta-chip.due-far{background:var(--bg-page);color:var(--text-secondary);border-color:transparent}
.tm-meta-chip.tm-stale{background:var(--yellow-bg);color:#8A6730;border-color:transparent;font-weight:600}

.tm-dep-link{display:flex;align-items:center;padding:7px 11px;background:var(--yellow-bg);border-radius:6px;margin-bottom:4px;font-size:14px;color:#8A6730;cursor:pointer;transition:background 150ms}
.tm-dep-link[data-dep-id]:hover{background:#F3E4C8}
.tm-dep-link .dep-arrow{color:var(--text-muted);margin-right:6px;white-space:nowrap;flex-shrink:0}
/* trailing go-arrow on the right — signals the row is a link even without hover */
.tm-dep-link .dep-go{margin-left:auto;padding-left:10px;color:var(--text-muted);flex-shrink:0}
.tm-dep-link[data-dep-id]:hover .dep-go{color:var(--accent)}
.tm-dep-link .dep-id{font-size:14px;color:var(--text-muted);font-family:var(--font-mono,monospace);
  margin-left:8px}

.tm-typespecific-grid{display:grid;grid-template-columns:minmax(140px,max-content) 1fr;
  gap:11px 28px;font-size:13px;line-height:1.45}
.tm-typespecific-key{color:var(--text-muted);font-weight:500}
.tm-typespecific-val{color:var(--text-secondary)}
.tm-tscontent-item{margin-bottom:10px}
.tm-tscontent-k{font-size:12px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.03em;margin-bottom:2px}
.tm-tscontent-v{font-size:15px;line-height:1.55;color:var(--text-primary);white-space:pre-wrap}

.tm-labels{display:flex;flex-wrap:wrap;gap:6px}
.tm-label-chip{font-size:15px;padding:3px 10px;border-radius:12px;background:#EEEEEC;
  color:var(--text-secondary)}

.tm-comment{padding:10px 12px;background:var(--bg-page);border-radius:6px;margin-bottom:8px}
.tm-comment-meta{font-size:15px;color:var(--text-muted);margin-bottom:4px}
.tm-comment-text{font-size:14px;color:var(--text-primary);line-height:1.5}

/* Event history rendered as a real timeline: a continuous rail with a dot per
   event. Filled accent dot = operator/system action; hollow ring = auto event. */
.tm-history-list{display:flex;flex-direction:column;gap:0;position:relative}
.tm-history-list::before{content:"";position:absolute;left:4px;top:15px;bottom:15px;
  width:2px;background:var(--border);border-radius:2px}
.tm-history-item{position:relative;font-size:14px;line-height:1.55;padding:7px 0 7px 26px;
  border:none;background:transparent;color:var(--text-secondary);border-radius:0}
.tm-history-item::before{content:"";position:absolute;left:0;top:11px;width:10px;height:10px;
  border-radius:50%;background:var(--accent);box-shadow:0 0 0 3px var(--bg-card);z-index:1}
.tm-history-item.auto::before{background:var(--bg-card);border:2px solid var(--border-strong);
  box-shadow:0 0 0 2px var(--bg-card)}
.tm-history-item .h-date{color:var(--text-muted);font-weight:500;font-family:var(--font-mono,monospace);
  font-size:12.5px;margin-right:9px}
.tm-history-item.auto{opacity:1}
.tm-history-item .h-src{display:inline-block;margin-left:8px;padding:1px 9px;border-radius:6px;font-size:12px;
  font-family:var(--font-mono,monospace);font-weight:600;background:var(--bg-page);color:var(--text-muted);border:1px solid var(--border)}
.tm-history-item .h-src-none{background:#F7D9D9;color:#8A1414;border:1px solid #E0A0A0}
.tm-history-item .h-auto{display:inline-block;margin-left:7px;padding:1px 8px;border-radius:6px;font-size:11.5px;
  font-weight:500;background:var(--bg-page);color:var(--text-muted);border:1px solid var(--border)}
.tm-action-status{padding:var(--space-sm) var(--space-md);margin:var(--space-sm) 0;
  border-radius:var(--radius-btn);font-size:14px;display:none}
.tm-action-status.show{display:block}
.tm-action-status.success{background:var(--green-bg);color:#3B5E2A;border-left:3px solid var(--accent-green)}
.tm-action-status.error{background:var(--red-bg);color:var(--accent-red);border-left:3px solid var(--accent-red)}
.tm-action-status.info{background:var(--blue-bg);color:#0C447C;border-left:3px solid var(--accent-blue)}
/* Hypothesis = the system thinking out loud, not a warning. Calm neutral card. */
.tm-assist-hyp{padding:13px 16px;background:var(--bg-subtle);border:1px solid var(--border);
  border-left:3px solid var(--border-strong);border-radius:10px;font-size:15px;line-height:1.6;
  color:var(--text-secondary);margin-bottom:12px;white-space:pre-wrap}
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
        <div class="tm-meta-row" id="tm-meta-row" style="display:none"></div>
        <div class="tm-section" id="tm-context-section" style="display:none">
          <div class="tm-section-label">__CONTEXT__</div>
          <div class="tm-section-body" id="tm-context-body"></div>
        </div>
        <div class="tm-section" id="tm-deps-section" style="display:none">
          <div class="tm-section-label">__DEPENDENCIES__</div>
          <div class="tm-section-body" id="tm-deps-body"></div>
        </div>
        <div class="tm-section" id="tm-blocks-section" style="display:none">
          <div class="tm-section-label">__BLOCKS__</div>
          <div class="tm-section-body" id="tm-blocks-body"></div>
        </div>
        <div class="tm-section" id="tm-assist-section" style="display:none">
          <div class="tm-section-label">__HYPOTHESIS__</div>
          <div class="tm-assist-hyp" id="tm-assist-hyp"></div>
        </div>
        <div class="tm-section" id="tm-next-section" style="display:none">
          <div class="tm-section-label">__NEXT_ACTION__</div>
          <div class="tm-next-action" id="tm-next-body"></div>
        </div>
        <div class="tm-section" id="tm-payroll-section" style="display:none">
          <div class="tm-section-label">__PAYROLL_RUN__</div>
          <div class="tm-section-body" id="tm-payroll-body"></div>
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
        <div class="tm-section tm-section-secondary" id="tm-typespecific-section" style="display:none">
          <div class="tm-section-label">__DETAILS__</div>
          <div class="tm-section-body" id="tm-typespecific-body"></div>
        </div>
        <div class="tm-actions">
          <div class="tm-actions-assist" id="tm-assist-btns"></div>
          <div class="tm-actions-generic">
            <button class="tm-btn" id="tm-discuss-btn" type="button">__BREAK_DOWN__</button>
          </div>
        </div>
        <div class="tm-action-status" id="tm-action-status"></div>
      </div>
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
    .replace('__BLOCKS__', t('🔓 Blocks'))
    .replace('__DETAILS__', t('📑 Details'))
    .replace('__DETAILS_CONTENT__', t('📋 Particulars'))
    .replace('__PAYROLL_RUN__', t('👥 Payroll run'))
    .replace('__COMMENTS__', t('💬 Comments'))
    .replace('__REPLY_DRAFT__', t('💬 Draft reply to client'))
    .replace('__BREAK_DOWN__', t('🔍 Break down'))
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
    // Collapse runs of spaces/tabs only — never newlines, so intentional line
    // breaks in context/hypothesis survive (the renderer shows them via pre-wrap).
    s = s.replace(/[ \t]{2,}/g, ' ');
    s = s.replace(/[ \t]+([.,;:)])/g, '$1');
    s = s.replace(/[ \t—–-]+$/gm, '');
    return s.trim();
  }

  // Readable label for an event source channel — mirrors _helpers.source_label
  // so the history timeline never shows a raw machine id (resolution_sweep,
  // chat_irina, morning_scan_…). Map is the single Python source, injected here.
  var SRC_LABELS = __SRC_LABELS_JSON__;
  function srcLabel(s){
    s = String(s||'').split(':')[0].trim();
    if(!s) return '';
    var ch = s.toLowerCase();
    if(Object.prototype.hasOwnProperty.call(SRC_LABELS, ch)) return SRC_LABELS[ch];
    var machine = ch.indexOf('_') >= 0 || /[0-9]/.test(ch) || /[a-z]/.test(ch);
    return machine ? '__SRC_GENERIC__' : s;
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
      statusDisp: card.getAttribute('data-track-status-disp') || '',
      statusCanon: card.getAttribute('data-track-status-canon') || '',
      source: card.getAttribute('data-track-source') || '',
      blockedByJson: card.getAttribute('data-track-blocked-by-json') || '[]',
      blocksJson: card.getAttribute('data-track-blocks-json') || '[]',
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
      // fallback: client name from the page header (client's own dashboard —
      // cards there carry client_id but no client_name)
      var h1 = document.querySelector('.client-topbar h1') || document.querySelector('h1');
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
    // The task context (facts) is immutable — kept in data-prompt-ctx so the
    // operator can clear/replace the default instruction (data-prompt) without
    // losing it. The unified modal always prepends the context to whatever is
    // in the editable field on copy.
    var _ctx = '__DISC_PRE__' + (currentTrack.title || '') + '__DISC_MID__' + (currentTrack.clientName || '') + '. ';
    if (currentTrack.context) _ctx += '__DISC_CTX__' + currentTrack.context + ' ';
    if (currentTrack.nextAction) _ctx += '__DISC_NEXT__' + currentTrack.nextAction + '. ';
    if (currentTrack.taskType) _ctx += '(task_type: ' + currentTrack.taskType + ') ';
    try { var _ts = JSON.parse(currentTrack.typeSpecificJson || '{}'); var _sp = []; if (_ts.period) _sp.push('period ' + _ts.period); if (_ts.amount != null) _sp.push('amount ' + _ts.amount); if (_sp.length) _ctx += '__DISC_SPEC__' + _sp.join(', ') + '. '; } catch (e) {}
    try { var _bb = JSON.parse(currentTrack.blockedByJson || '[]'); if (_bb.length) _ctx += '__DISC_BLOCK__' + _bb.map(function(x){ return x.title || x.id || x; }).join(', ') + '. '; } catch (e) {}
    try { var _h = JSON.parse(currentTrack.historyJson || '[]'); if (_h.length) { var _last = _h.slice(-2).map(function(ev){ return (ev.date ? ev.date + ' ' : '') + (ev.event || ''); }); _ctx += '__DISC_DONE__' + _last.join('; ') + '. '; } } catch (e) {}
    try { var _a = currentTrack.assistJson ? JSON.parse(currentTrack.assistJson) : null; if (_a && _a.hypothesis) _ctx += '__DISC_HYP__' + _a.hypothesis + ' '; } catch (e) {}
    btnDiscuss.setAttribute('data-prompt-ctx', _ctx.trim());
    btnDiscuss.setAttribute('data-prompt', '__DISC_ASK__');
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
        // Operator-facing: localise the confidence word and humanise the ISO
        // update date (2026-06-13 -> "13 июня 2026"), same RU month names as the
        // history block uses (fmtWhen).
        var _CONF = {high:'уверенность: высокая', medium:'уверенность: средняя', low:'уверенность: низкая'};
        var _cf = _assist.confidence ? (_CONF[_assist.confidence] || ('уверенность: ' + _assist.confidence)) : '';
        var _ua = (_assist.updated_at || '').trim();
        if(/^\d{4}-\d{2}-\d{2}/.test(_ua)){
          var _M=['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];
          _ua = parseInt(_ua.slice(8,10),10) + ' ' + _M[parseInt(_ua.slice(5,7),10)-1] + ' ' + _ua.slice(0,4);
        }
        _conf = '<span class="tm-assist-conf">(' + esc([_cf, _ua].filter(Boolean).join(' · ')) + ')</span>';
      }
      elAssistHyp.innerHTML = esc(stripIds(_assist.hypothesis)) + _conf;
      if(elAssistSec) elAssistSec.style.display = '';
      if(elNextSec) elNextSec.style.display = 'none';
    } else if(elAssistSec){ elAssistSec.style.display = 'none'; }
    var _hasAssistActions = !!(_assist && _assist.actions && _assist.actions.length && elAssistBtns);
    if(_hasAssistActions){
      var _attr = function(s){ return String(s||'').replace(/[&<>"]/g, function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); };
      elAssistBtns.innerHTML = _assist.actions.map(function(a, i){
        return '<button class="tm-btn' + (a.recommended ? ' tm-btn-primary' : '') + '" data-prompt="' + _attr(a.prompt || '') + '" data-prompt-ctx="' + _attr(_ctx.trim()) + '">' + esc(stripIds(a.label || '') || ('__ACTION__ ' + (i+1))) + '</button>';
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
    if(currentTrack.statusRaw || currentTrack.statusDisp){
      // Localized, normalized label (Python collapses free-form statuses to a
      // canonical token + Russian label); CSS class follows the canonical bucket.
      var statusTxt = currentTrack.statusDisp || currentTrack.statusRaw;
      var statusCls = 'status-' + (currentTrack.statusCanon || currentTrack.statusRaw.replace('awaiting_external', 'awaiting'));
      metaChips.push('<span class="tm-meta-chip ' + statusCls + '">●&nbsp;' + esc(statusTxt) + '</span>');
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
    // Period — surfaced as a header chip (moved out of the Details rail)
    try {
      var _tsP = JSON.parse(currentTrack.typeSpecificJson || '{}');
      if(_tsP.period){
        var _pv = String(_tsP.period), _pl = _pv;
        var _pm = /^(\d{4})-(\d{2})$/.exec(_pv);
        var _MO = ['январь','февраль','март','апрель','май','июнь','июль','август','сентябрь','октябрь','ноябрь','декабрь'];
        if(_pm){ var _mi = parseInt(_pm[2],10); if(_mi>=1 && _mi<=12) _pl = _MO[_mi-1] + ' ' + _pm[1]; }
        else { var _pq = /^(\d{4})-Q([1-4])$/i.exec(_pv); if(_pq) _pl = 'Q' + _pq[2] + ' ' + _pq[1]; }
        metaChips.push('<span class="tm-meta-chip">' + esc(_pl) + '</span>');
      }
    } catch(e){}
    if(currentTrack.due){
      // THE shared due badge (.due-badge) — same chip as the hero and the plan
      var _d = String(currentTrack.due).toLowerCase(), dueCls = 'far';
      if(_d.indexOf('overdue') >= 0 || _d.indexOf('просроч') >= 0) dueCls = 'overdue';
      else if(_d.indexOf('today') >= 0 || _d.indexOf('сегодня') >= 0) dueCls = 'today';
      else if(_d.indexOf('tomorrow') >= 0 || _d.indexOf('завтра') >= 0 || _d.match(/in [1-7]d/) || _d.match(/через [1-7] /)) dueCls = 'soon';
      metaChips.push('<span class="due-badge due-badge-' + dueCls + '">' + esc(currentTrack.due) + '</span>');
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
          // clickable: jumps to the blocker's own task card (handler below)
          return '<div class="tm-dep-link" data-dep-id="' + esc(d.id || '') + '">' +
            '<span class="dep-arrow">&#128274;</span>' + esc(dt) +
            '<span class="dep-go">&rarr;</span>' +
          '</div>';
        }).join('');
        elDepsSec.style.display = '';
      } else { elDepsSec.style.display = 'none'; }
    } catch(e) { elDepsSec.style.display = 'none'; }

    // Blocks (reverse deps — the tasks THIS one is holding up)
    var elBlocksSec = document.getElementById('tm-blocks-section');
    var elBlocksBody = document.getElementById('tm-blocks-body');
    try {
      var bl = JSON.parse(currentTrack.blocksJson);
      if(bl && bl.length){
        elBlocksBody.innerHTML = bl.map(function(d){
          var dt = d.title || '';
          if(!dt || dt === d.id) dt = '__RELATED_TASK__';
          // clickable: jumps to the blocked task's own card (shared handler below)
          return '<div class="tm-dep-link" data-dep-id="' + esc(d.id || '') + '">' +
            '<span class="dep-arrow">&#128275;</span>' + esc(dt) +
            '<span class="dep-go">&rarr;</span>' +
          '</div>';
        }).join('');
        elBlocksSec.style.display = '';
      } else { elBlocksSec.style.display = 'none'; }
    } catch(e) { elBlocksSec.style.display = 'none'; }

    // Type-specific details
    var elTsSec = document.getElementById('tm-typespecific-section');
    var elTsBody = document.getElementById('tm-typespecific-body');
    try {
      var ts = JSON.parse(currentTrack.typeSpecificJson);
      var keys = Object.keys(ts || {});
        // Payroll run — render type_specific.payroll_lines as a table (entity-linking: the
        // per-employee calc rides the payroll task). Labels are locale-injected via PL.
        (function(){
          var elPaySec = document.getElementById('tm-payroll-section');
          var elPayBody = document.getElementById('tm-payroll-body');
          if(!elPaySec || !elPayBody) return;
          var _box = elPaySec.closest('.track-modal-box');
          if(_box) _box.classList.remove('tm-wide');
          var pl = ts.payroll_lines;
          if(!Array.isArray(pl) || !pl.length){ elPaySec.style.display='none'; return; }
          var PL = __PAY_L10N_JSON__;
          function n(v){ return (v==null?0:v).toLocaleString('ru-RU'); }
          // BPJS coverage — calm dot + label, no per-row yellow (the aggregate gap
          // lives once in the band). Posted = green dot, absent = muted dot.
          function kas(lbl, kc){
            var posted = kc && ((kc.employee||0)||(kc.employer||0));
            return '<span class="tm-pay-kas'+(posted?'':' off')+'"><i></i>'+lbl+'</span>';
          }
          // header band (review cockpit roll-up)
          var sm = ts._summary, band='';
          if(sm){
            var bp=['<span class="tm-band-i"><b>'+sm.n+'</b> '+PL.lines+'</span>',
                    '<span class="tm-band-sep"></span><span class="tm-band-i">\u03A3 PPh <b>'+n(sm.sum_pph)+'</b></span>'];
            if(sm.period_pph!=null) bp.push('<span class="tm-band-sep"></span><span class="tm-band-i">Предшественник <b>'+n(sm.period_pph)+'</b></span>');
            if(sm.gap) bp.push('<span class="tm-band-sep"></span><span class="tm-band-gap">\u2212'+n(Math.abs(sm.gap))+(sm.thr?' \u00B7 THR':'')+'</span>');
            if(sm.bpjs_gap) bp.push('<span class="tm-band-sep"></span><span class="tm-band-flag"><i></i>'+PL.socgap+'</span>');
            band='<div class="tm-pay-band">'+bp.join('')+'</div>';
          }
          var sumPph=0, sumNet=0;
          var rows = pl.map(function(l){
            sumPph += (l.pph||0); sumNet += (l.net||0);
            var rv=l._review||{}, b=(l.bpjs||{});
            var dch='';
            if(rv.is_new) dch=' <span class="tm-pay-delta">'+PL.newL+'</span>';
            else if(rv.delta){ dch=' <span class="tm-pay-delta">'+(rv.delta>0?'+':'\u2212')+n(Math.abs(rv.delta))+'</span>'; }
            var thrsub = l.thr ? '<div class="tm-pay-sub2">'+PL.thr+' '+n(l.thr)+'</div>' : '';
            var flagged = rv.flag;
            var sv = flagged ? '<span class="tm-pay-pill tm-pay-warn">'+PL.review+'</span>' : '';
            return '<tr><td>'+
              '<div class="tm-pay-name">'+esc(l.name||l.employee_id||'?')+dch+'</div>'+
              '<div class="tm-pay-sub">'+(l.position?esc(l.position):'')+
              (l.method?'<span class="tm-pay-tag">'+esc(l.method)+'</span>':'')+'</div></td>'+
              '<td class="num">'+n(l.gross)+thrsub+'</td><td class="num">'+n(l.pph)+'</td>'+
              '<td><span class="tm-pay-kasrow">'+kas('Kes',b.kesehatan)+kas('Ket',b.ketenagakerjaan)+'</span></td>'+
              '<td class="num">'+n(l.net)+'</td><td>'+sv+'</td></tr>';
          }).join('');
          var tot = ts.totals||{};
          var foot = '<tr class="tm-pay-foot"><td>'+PL.total+' ('+pl.length+')</td><td></td><td class="num">'+
            n(tot.pph!=null?tot.pph:sumPph)+'</td><td></td><td class="num">'+n(tot.net!=null?tot.net:sumNet)+'</td><td></td></tr>';
          elPayBody.innerHTML = band+'<table class="tm-pay-table"><thead><tr><th>'+PL.emp+'</th><th class="num">'+PL.gross+'</th>'+
            '<th class="num">PPh</th><th>BPJS</th><th class="num">'+PL.net+'</th><th>'+PL.check+'</th></tr></thead><tbody>'+
            rows+'</tbody><tfoot>'+foot+'</tfoot></table>';
          if(_box) _box.classList.add('tm-wide');
          elPaySec.style.display='';
        })();
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
          remaining_operations: 'Operations remaining', account_id: 'Account', blocking_what: 'Blocking what', dismissed_at: 'Dropped', dismissed_by: 'Dropped by', dismissed_note: 'Drop note', finkoper_tasks: 'Finkoper tasks', finkoper_task_url: 'Task link', change_date: 'Change date', auditor: 'Auditor', reminder_at: 'Reminder', debit: 'Debit', credit: 'Credit', balance_end: 'Closing balance', paid_outside_rs: 'Paid outside account', accounts_to_review: 'Accounts to review', period_covered: 'Period covered', control_check_at: 'Control check', status_detail: 'Status detail', investigation_steps: 'Investigation steps', memory_refs: 'Memory references', check_cycles: 'Check cycles', loaded_until: 'Loaded until', balance_at_loaded: 'Balance at load', remaining_period: 'Remaining period', kassas_ids: 'Cash registers', owner_role: 'Assignee role', kkt_status: 'Cash register status', pending_corrections_amount: 'Amount to correct', law_basis_penalty: 'Statute (penalty)', law_basis_escape: 'Statute (exemption)', monitor_url: 'Monitoring link', target_regime: 'Target regime', okved: 'OKVED', regions_candidate: 'Candidate regions', estimated_economy_per_year_rub: 'Yearly savings, ₽', psn_cost_spb_2026_per_vehicle_rub: 'SPb 2026 patent per vehicle, ₽', spn_income_limit_2026_rub: 'Income limit 2026, ₽', application_deadline_for_2026_07_01_start: 'Application deadline for 2026-07-01 start', application_form: 'Application form', taxi_permit_law: 'Taxi permit law', pending_client_answers: 'Awaiting client answers', recommended_combo: 'Recommended combination', package_files_count: 'Files in package', contract: 'Contract', may_act_available_after: 'May statement available after', requested_systems: 'Requested systems', check_items: 'Check items', yearly_fixed: 'Yearly fixed contribution', period_from: 'Period from', period_to: 'Period to', tax_amount_may_2026: 'Tax for May 2026', blocker_resolution: 'Blocker resolution',
          doc_expected: 'Document expected', deadline: 'Deadline', decision: 'Decision', next_step: 'Next step', amount_paid: 'Amount paid', payment_basis: 'Payment basis', service_quarter: 'Service quarter', tariff_note: 'Tariff note', wake_date: 'Resume on', wake_to: 'Dormant until', jur_services: 'Legal services', condition: 'Condition', contract_termination_date: 'Contract termination date', activation: 'Activation', advance_calc_gross: 'Advance calc (gross)', advance_due_q1: 'Advance due Q1', filled_through: 'Filled through', form_when: 'Form when', last_verified_period: 'Last verified period', legal_basis: 'Legal basis', payer: 'Payer', payment_tranches: 'Payment tranches', reconciliation_status: 'Reconciliation status', review_date: 'Review date', threshold_law: 'Threshold statute', q1_2026_paid: 'Q1 2026 paid', q4_2025_paid: 'Q4 2025 paid'
        };
        var TS_RU_LOC = __TS_RU_LOC_JSON__;
        var TS_INTERNAL = __TS_INTERNAL_JSON__;
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
        // Humanize machine values for the Properties block: period strings
        // (YYYY-MM / YYYY-Qn) render as readable RU; a small curated gloss covers
        // the common machine enums; anything unknown falls back to the raw value.
        var _MONTHS_RU=['январь','февраль','март','апрель','май','июнь','июль','август','сентябрь','октябрь','ноябрь','декабрь'];
        var _TS_VAL={
          'monthly_in_correction_window_01_07':'ежемесячно · окно корректировки 01–07',
          'ausn_critical':'АУСН · критично'
        };
        function _periodHuman(s){
          var m=/^(\d{4})-(\d{2})$/.exec(s);
          if(m){ var mo=parseInt(m[2],10); if(mo>=1&&mo<=12) return _MONTHS_RU[mo-1]+' '+m[1]; }
          var q=/^(\d{4})-Q([1-4])$/i.exec(s);
          if(q) return 'Q'+q[2]+' '+q[1];
          return null;
        }
        function _tsFmt(v){
          if(Array.isArray(v)) return v.join(', ');
          if(typeof v === 'number') return v.toLocaleString('ru-RU');
          var s=String(v);
          if(_TS_VAL[s]) return _TS_VAL[s];
          var ph=_periodHuman(s); if(ph) return ph;
          return s;
        }
        var propRows = [], contentRows = [];
        keys.filter(function(k){return ts[k] !== null && ts[k] !== '' && TS_INTERNAL.indexOf(k) < 0 && ['payroll_lines','totals','review','period'].indexOf(k) < 0;}).forEach(function(k){
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
    var RU_MON=['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];
    function fmtWhen(h){
      var s=(h.ts||h.date||'').trim(); if(s.length<10) return s;
      var dd=parseInt(s.slice(8,10),10), mm=parseInt(s.slice(5,7),10);
      if(!mm||mm<1||mm>12) return s;
      var out=dd+' '+RU_MON[mm-1];
      if(s.indexOf('T')>=0 && s.length>=16) out+=', '+s.slice(11,16);
      return out;
    }
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
          var src = (h.source || h.by || '').trim();
          var srcHtml = src ? '<span class="h-src">' + esc(srcLabel(src)) + '</span>' : '';
          var autoHtml = h.auto ? '<span class="h-auto">__AUTO__</span>' : '';
          return '<div class="tm-history-item' + autoCls + '">' +
            '<span class="h-date">' + esc(fmtWhen(h)) + '</span>' +
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

  document.addEventListener('click', function(e){
    var inner = e.target.closest('button,a');
    if(inner) return;
    // a dependency chip (modal «Зависимости», plan/card rows): jump to the
    // blocker's own task card if it's rendered anywhere on the page.
    var dep = e.target.closest('[data-dep-id]');
    if(dep){
      var did = dep.getAttribute('data-dep-id');
      var sel = (window.CSS && CSS.escape) ? CSS.escape(did) : did;
      var bcard = did && document.querySelector('.track-card-clickable[data-track-id="' + sel + '"]');
      if(bcard){ e.preventDefault(); e.stopPropagation(); openTrackModal(bcard); return; }
    }
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
    .replace('__PRIO_HIGH__', t('high priority'))
    .replace('__PRIO_LOW__', t('low priority'))
    .replace('__STALE_FOR__', t('stale for'))
    .replace('__D_UNIT__', t('d'))
    .replace('__RELATED_TASK__', t('Related task'))
    .replace('__ACTION__', t('Action'))
    .replace('__AUTO__', t('auto'))
    .replace('__SRC_LABELS_JSON__', json.dumps(_SRC_LABELS, ensure_ascii=False))
    .replace('__SRC_GENERIC__', _SRC_GENERIC)
    .replace('__TS_RU_LOC_JSON__', _ts_ru_loc_json())
    .replace('__TS_INTERNAL_JSON__', _ts_internal_json())
    .replace('__PAY_L10N_JSON__', _pay_l10n_json())
    # Context labels — pure facts, no instruction verbs (the runtime's standing
    # procedure lives in policies/INSTRUCTIONS.md, not in the copied prompt).
    .replace('__DISC_PRE__', _loc('Task: "', 'Задача: «'))
    .replace('__DISC_MID__', _loc('" · client ', '» · клиент '))
    .replace('__DISC_CTX__', _loc('Situation: ', 'Ситуация: '))
    .replace('__DISC_NEXT__', _loc('Planned next step: ', 'Следующий шаг: '))
    .replace('__DISC_SPEC__', _loc('Specifics: ', 'Детали: '))
    .replace('__DISC_BLOCK__', _loc('Blocked by: ', 'Блокирует: '))
    .replace('__DISC_DONE__', _loc('Already done: ', 'Уже сделано: '))
    .replace('__DISC_HYP__', _loc('Working hypothesis: ', 'Гипотеза: '))
    # The editable default is just the per-task ask. The standing rules (resolve
    # jurisdiction, checklist, verify, mm_update + approval, nothing outward
    # without OK) are already what the runtime follows from policies.
    .replace('__DISC_ASK__', _loc(
        'Break down the task and propose a concrete next action.',
        'Разбери задачу и предложи конкретное следующее действие.'))
)
