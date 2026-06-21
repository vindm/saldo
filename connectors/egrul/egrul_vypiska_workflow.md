# Company registry (EGRIP) — downloading statements via Chrome (canonical pipeline)

**Recorded: 2026-05-24**

## Summary

egrul.nalog.ru — a search form by INN or OGRNIP.
The "GET STATEMENT" button downloads a PDF.
File name: `fl-{OGRNIP}-{YYYYMMDDHHMMSS}.pdf`
Read it via PDF Tools MCP using the direct path from Downloads.

---

## Pipeline — step by step

### 1. Open a tab

```
navigate tabId → https://egrul.nalog.ru/index.html
```
Check readiness: `document.querySelector('#query')` — must return the input.

---

### 2. Single client — reliable variant (10 sec)

```javascript
(async () => {
  const input = document.querySelector('#query');
  const searchBtn = document.querySelector('.btn-search');
  input.value = 'OGRNIP_OR_INN';
  input.dispatchEvent(new Event('input', {bubbles:true}));
  searchBtn.click();
  await new Promise(r => setTimeout(r, 4000));   // wait for result
  const dlBtn = document.querySelector('button.btn-excerpt');
  if (!dlBtn) return 'no button';
  dlBtn.click();
  await new Promise(r => setTimeout(r, 6000));   // wait for PDF download
  return 'done';
})()
```

**Minimums:** 4 sec search + 6 sec after click. Any less — the file does not finish saving.

---

### 3. Batch — up to 3 clients per call (≤45 sec Chrome MCP timeout)

```javascript
(async () => {
  const ogrnipy = ['OGRNIP1', 'OGRNIP2', 'OGRNIP3'];
  const input = document.querySelector('#query');
  const searchBtn = document.querySelector('.btn-search');
  const res = [];
  for (let i = 0; i < ogrnipy.length; i++) {
    input.value = ogrnipy[i];
    input.dispatchEvent(new Event('input', {bubbles:true}));
    searchBtn.click();
    await new Promise(r => setTimeout(r, 3500));
    const dlBtn = document.querySelector('button.btn-excerpt');
    if (dlBtn) { dlBtn.click(); res.push('ok_' + i); }
    else res.push('no_' + i);
    await new Promise(r => setTimeout(r, 3000));
  }
  return res.join(',');
})()
```

For 4+ clients — do several calls, 3 at a time.

---

### 4. Find the downloaded files

```
list_pdfs(directory="C:\Users\user\Downloads")
grep "fl-.*YYYYMMDD"   // filter by today's date
```

Path to the file: `C:\Users\user\Downloads\fl-{OGRNIP}-{timestamp}.pdf`

> The Downloads mount via Linux bash does NOT work (I/O error on ls/find).
> Always use PDF Tools MCP list_pdfs or a direct read_pdf_content.

---

### 5. Read details and OKVED codes

```
read_pdf_content(pdf_path="C:\Users\user\Downloads\fl-OGRNIP-timestamp.pdf", max_pages=4)
```

| Page | Contents |
|---|---|
| 1 | Full name, OGRNIP, INN, registration date, registering tax office (IFTS) |
| 2–3 | Primary OKVED (p. 21) + additional ones (pp. 23, 25, 27...) |
| 4+ | History of company registry records |

Fields in the statement:
- p. 6 → SP email (if provided)
- p. 8 → OGRNIP
- p. 9 → Registration date
- p. 10–11 → Registering tax office (IFTS) + its address
- p. 13 → INN
- p. 21 → Primary OKVED
- p. 23, 25... → Additional OKVED codes

---

## Limitations

| Problem | What to do |
|---|---|
| Chrome = read-tier, clicks blocked | Click via JS: `element.click()` in javascript_tool |
| `[BLOCKED: Cookie/query string data]` | Do not return INN/OGRNIP in the result JS — only the structure |
| Downloads mount not readable via ls | Only PDF MCP list_pdfs or read_pdf_content by exact path |
| SP address is not disclosed | The public statement since ~2020 hides the home address; only the region |
| Duplicate files | If clicked several times — take the most recent (largest timestamp) |

---

## Python — bulk update of client cards

```python
import re

def replace_field(content, field, new_value):
    pattern = r'(\| ' + re.escape(field) + r' \| )([^|]+)(\|)'
    replacement = r'\g<1>' + new_value + r' \3'
    return re.sub(pattern, replacement, content)

# For each card:
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
for field, value in data.items():
    content = replace_field(content, field, value)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
```

Works for fields in the `| Field | Value |` format in Markdown tables.
