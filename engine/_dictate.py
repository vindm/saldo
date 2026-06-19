"""_dictate.py — "🎤 Dictate" button on dashboard cards.

Version 2 (2026-05-17): no Web Speech API; dictation via the system Win+H.

Reason: dashboards open over file://, which has no stable origin, so
Chrome/Edge don't remember the microphone permission between loads.
The "microphone in use" popup would appear on every click.

Solution: the modal stays as a context wrapper with a textarea. The user
opens the modal, focus lands in the field automatically, they press Win+H
and dictate the thought with Windows system dictation. Then "Copy as prompt"
assembles the card context + the dictated text and puts it on the clipboard.

Render helper: render_dictate_button(kind, ...) returns a ready <button>
with the right data attributes (data-mic="1" + data-mic-kind/id/client/title/extra).
"""

from _helpers import _esca
from _strings import t


DICTATE_CSS = (
    # .btn-mic — marker for JS. Styles only for legacy .btn-mini.btn-mic (no !important)
    ".btn-mini.btn-mic{background:#eaf2f4;border-color:#cfe1e6;color:#4a7c89}"
    ".btn-mini.btn-mic:hover{background:#d8e8eb;border-color:#4a7c89;color:#3d6772}"
    ".mic-modal{position:fixed;inset:0;background:rgba(0,0,0,0.45);z-index:10000;"
    "display:none;align-items:center;justify-content:center;padding:16px}"
    ".mic-modal.open{display:flex}"
    ".mic-modal-box{background:#fff;border-radius:8px;padding:24px;"
    "max-width:640px;width:100%;max-height:88vh;overflow-y:auto;"
    "box-shadow:0 10px 40px rgba(0,0,0,0.2);font-family:inherit}"
    ".mic-modal-title{font-size:18px;font-weight:500;margin:0 0 4px;color:#1f2937}"
    ".mic-modal-sub{font-size:15px;color:#6b7280;margin-bottom:16px}"
    ".mic-context{background:#eaf2f4;padding:10px 14px;border-radius:4px;"
    "font-size:15px;color:#406570;margin-bottom:16px;border-left:3px solid #4a7c89;"
    "line-height:1.45}"
    ".mic-context strong{color:#4a7c89}"
    ".mic-textarea{width:100%;min-height:160px;padding:12px;border:1px solid #e5e7eb;"
    "border-radius:4px;font-family:inherit;font-size:14px;line-height:1.5;"
    "resize:vertical;margin-bottom:12px;box-sizing:border-box}"
    ".mic-textarea:focus{outline:none;border-color:#4a7c89}"
    ".mic-btn{padding:7px 14px;border:1px solid #e5e7eb;background:#fff;color:#1f2937;"
    "border-radius:4px;cursor:pointer;font-size:15px;font-family:inherit;"
    "transition:background .15s}"
    ".mic-btn:hover{background:#f3f1ec}"
    ".mic-btn-copy{background:#4a7c89;color:#fff;border-color:#4a7c89}"
    ".mic-btn-copy:hover{background:#3d6772}"
    ".mic-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}"
    ".mic-copy-status{display:none;padding:10px 12px;background:#e8f3ec;"
    "color:#356544;border-radius:4px;margin-top:12px;font-size:15px}"
    ".mic-copy-status.active{display:block}"
    ".mic-copy-status strong{display:block;margin-bottom:4px}"
    ".mic-hint{font-size:15px;color:#9ca3af;margin-top:14px;padding-top:12px;"
    "border-top:1px solid #e5e7eb;line-height:1.55}"
    ".mic-hint kbd{background:#f3f4f6;border:1px solid #d1d5db;border-radius:3px;"
    "padding:1px 5px;font-family:ui-monospace,monospace;font-size:15px;color:#374151}"
)


DICTATE_MODAL_HTML = (
    '<div id="mic-modal" class="mic-modal">'
    '<div class="mic-modal-box" onclick="event.stopPropagation()">'
    '<div class="mic-modal-title">🎤 ' + t('Dictate your thoughts') + '</div>'
    '<div class="mic-modal-sub">' + t('Press <kbd>Win</kbd>+<kbd>H</kbd> in the field and speak — or type by hand.') + '</div>'
    '<div id="mic-context" class="mic-context"></div>'
    '<textarea id="mic-textarea" class="mic-textarea" '
    'placeholder="' + t('Press Win+H and dictate here…') + '"></textarea>'
    '<div id="mic-copy-status" class="mic-copy-status">'
    '<strong>✓ ' + t('Prompt copied to clipboard') + '</strong>'
    + t('Switch to the chat with Claude and paste (Ctrl+V).') +
    '</div>'
    '<div class="mic-actions">'
    '<button id="mic-btn-copy" class="mic-btn mic-btn-copy" type="button">📋 ' + t('Copy as prompt') + '</button>'
    '<button id="mic-btn-close" class="mic-btn" type="button">' + t('Close') + '</button>'
    '</div>'
    '<div class="mic-hint">'
    + t('Tip: <kbd>Win</kbd>+<kbd>H</kbd> is the built-in Windows dictation, it works in any text field. The card context is automatically appended to the copied prompt.') +
    '</div>'
    '</div>'
    '</div>'
)


DICTATE_JS = (
    '<script>'
    '(function(){'
    'var modal=document.getElementById("mic-modal");'
    'var ta=document.getElementById("mic-textarea");'
    'var ctxBox=document.getElementById("mic-context");'
    'var btnCopy=document.getElementById("mic-btn-copy");'
    'var btnClose=document.getElementById("mic-btn-close");'
    'var copyStatus=document.getElementById("mic-copy-status");'
    'var currentCtx=null;'
    'function escapeHtml(s){if(!s)return"";return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}'
    'function openMic(btn){'
    'currentCtx={'
    'kind:btn.getAttribute("data-mic-kind")||"note",'
    'id:btn.getAttribute("data-mic-id")||"",'
    'client:btn.getAttribute("data-mic-client")||"",'
    'title:btn.getAttribute("data-mic-title")||"",'
    'extra:btn.getAttribute("data-mic-extra")||""'
    '};'
    'var ctxParts=[];'
    'if(currentCtx.id)ctxParts.push("<strong>"+escapeHtml(currentCtx.id)+"</strong>");'
    'if(currentCtx.client)ctxParts.push(escapeHtml(currentCtx.client));'
    'if(currentCtx.kind)ctxParts.push("<em>"+escapeHtml(currentCtx.kind)+"</em>");'
    'var titleLine=currentCtx.title?"<br><em style=\\"font-size:15px\\">"+escapeHtml(currentCtx.title)+"</em>":"";'
    'ctxBox.innerHTML=(ctxParts.join(" · ")||"general thought")+titleLine;'
    'ta.value="";'
    'copyStatus.classList.remove("active");'
    'modal.classList.add("open");'
    'setTimeout(function(){ta.focus();},20);'
    '}'
    'function closeMic(){modal.classList.remove("open");}'
    'function copyPrompt(){'
    'var text=ta.value.trim();'
    'if(!text){alert("Dictate or type your thoughts first.");return;}'
    'var lines=["Context from the dashboard:"];'
    'if(currentCtx.kind)lines.push("- Type: "+currentCtx.kind);'
    'if(currentCtx.id)lines.push("- ID: "+currentCtx.id);'
    'if(currentCtx.client)lines.push("- Client: "+currentCtx.client);'
    'if(currentCtx.title)lines.push("- Title: "+currentCtx.title);'
    'if(currentCtx.extra)lines.push("- Context: "+currentCtx.extra);'
    'lines.push("");lines.push("My thoughts:");lines.push(text);'
    'var prompt=lines.join("\\n");'
    'var tmp=document.createElement("textarea");'
    'tmp.value=prompt;'
    'tmp.style.position="fixed";tmp.style.left="-9999px";tmp.style.opacity="0";'
    'document.body.appendChild(tmp);tmp.focus();tmp.select();'
    'var ok=false;try{ok=document.execCommand("copy");}catch(e){ok=false;}'
    'document.body.removeChild(tmp);'
    'if(ok){copyStatus.classList.add("active");ta.focus();}'
    'else{ta.value=prompt;alert("Auto-copy failed. The prompt is in the field — select and copy it manually (Ctrl+A → Ctrl+C).");}'
    '}'
    'btnCopy.addEventListener("click",copyPrompt);'
    'btnClose.addEventListener("click",closeMic);'
    'modal.addEventListener("click",function(e){if(e.target===modal)closeMic();});'
    'document.addEventListener("click",function(e){'
    'var b=e.target.closest("button[data-mic]");'
    'if(b){e.preventDefault();e.stopPropagation();openMic(b);}'
    '});'
    'document.addEventListener("keydown",function(e){'
    'if(e.key==="Escape"&&modal.classList.contains("open"))closeMic();'
    '});'
    'window.openMicModal=function(opts){'
    'opts=opts||{};'
    'var fake={getAttribute:function(k){'
    'var key=k.replace("data-mic-","");'
    'return (opts[key]==null?"":String(opts[key]));'
    '}};'
    'openMic(fake);'
    '};'
    '})();'
    '</script>'
)


def render_dictate_button(kind, id="", client="", title="", extra="", btn_class="btn-mini"):
    """Ready <button class="btn-mic"> with the right data-mic-* attributes."""
    return (
        f'<button class="{btn_class} btn-mic" type="button" data-mic="1" '
        f'data-mic-kind="{_esca(kind)}" '
        f'data-mic-id="{_esca(id)}" '
        f'data-mic-client="{_esca(client)}" '
        f'data-mic-title="{_esca(title)}" '
        f'data-mic-extra="{_esca(extra)}" '
        f'title="{_esca(t("Dictate thoughts about this"))}">🎤 {t("Dictate")}</button>'
    )
