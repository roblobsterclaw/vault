from pathlib import Path
from datetime import datetime
import json, re, shutil, hashlib

workspace = Path('/Users/joemac/.openclaw/workspace')
repo = workspace / 'projects' / 'vault'
if repo.exists():
    for item in repo.iterdir():
        if item.name == '.git':
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
else:
    repo.mkdir(parents=True)

folders = {
    'tuckerton-group': 'Tuckerton Group',
    'investing': 'Investing',
    'rebolt': 'ReBolt',
    'firehouse': 'Firehouse',
    'real-estate': 'Real Estate',
    'family': 'Family',
    'lobster-press': 'Lobster Press',
    'research': 'Research',
    'daily-rundowns': 'Daily Rundowns',
}
for slug in folders:
    (repo / 'docs' / slug).mkdir(parents=True, exist_ok=True)

roots = [workspace, workspace/'projects', workspace/'reports']
exts = {'.docx', '.pdf', '.xlsx'}
cut = datetime.now().timestamp() - 60*24*3600
seen_real = set()
files = []
for root in roots:
    if not root.exists():
        continue
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        parts = set(p.parts)
        if 'vault' in parts or 'node_modules' in parts or '.git' in parts:
            continue
        try:
            real = str(p.resolve())
            st = p.stat()
        except OSError:
            continue
        if real in seen_real or st.st_mtime < cut:
            continue
        seen_real.add(real)
        files.append((st.st_mtime, st.st_size, p))
files.sort(reverse=True)

def classify(path: Path):
    s = str(path).lower()
    if any(k in s for k in ['daily/', 'morning', 'rundown', 'mission_control', 'mission-control', 'ttd', 'jfl-ttd']):
        return 'daily-rundowns'
    if any(k in s for k in ['rebolt', 'patent', 'provisional', 'prior-art']):
        return 'rebolt'
    if any(k in s for k in ['lobster-press', 'social-media', 'cassidys', 'content', 'brand-guide']):
        return 'lobster-press'
    if any(k in s for k in ['firehouse', '18-new', 'new-street', 'renovation']):
        return 'firehouse'
    if any(k in s for k in ['invest', 'mose', 'portfolio', 'truist', '13f', 'margin', 'compensation', 'roth', 'financial', 'stock']):
        return 'investing'
    if any(k in s for k in ['real-estate', 'vacation', 'rental', 'carolina', 'ship-bottom', 'property', 'lease']):
        return 'real-estate'
    if any(k in s for k in ['family', 'danielle', 'juliana', 'isabella', 'keli', 'school', 'health', 'dermatitis', 'cassidy']):
        return 'family'
    if any(k in s for k in ['tlc', 'tuckerton', 'surfbox', 'health-insurance', 'meeting', 'contractor', 'quote', 'vendor', 'insurance']):
        return 'tuckerton-group'
    return 'research'

def clean_title(path: Path):
    stem = re.sub(r'[_-]+', ' ', path.stem).strip()
    stem = re.sub(r'\s+', ' ', stem)
    return stem

def version_key(name):
    stem = Path(name).stem.lower()
    stem = re.sub(r'\b(v\d+(?:\.\d+)?|final|latest|draft|clean|copy|updated|revised|formatted|print|baseline|working|from[-_ ]joe|joeedits|edits|\d{4}-\d{2}-\d{2}|\d{8}|[a-f0-9]{8})\b', '', stem)
    stem = re.sub(r'[^a-z0-9]+', ' ', stem)
    return re.sub(r'\s+', ' ', stem).strip() or Path(name).stem.lower()

manifest = []
used = set()
for mtime, size, src in files:
    folder = classify(src)
    safe = re.sub(r'[^A-Za-z0-9._-]+', '-', src.name).strip('-')
    dest_name = safe
    if (folder, dest_name.lower()) in used:
        h = hashlib.sha1(str(src).encode()).hexdigest()[:8]
        dest_name = f"{Path(safe).stem}-{h}{src.suffix.lower()}"
    used.add((folder, dest_name.lower()))
    dest = repo / 'docs' / folder / dest_name
    shutil.copy2(src, dest)
    date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    manifest.append({
        'name': clean_title(src),
        'fileName': dest_name,
        'folder': folder,
        'department': folders[folder],
        'date': date,
        'type': src.suffix.lower().lstrip('.'),
        'size': size,
        'url': f'docs/{folder}/{dest_name}',
        'description': f"{folders[folder]} document copied from {src.parent.name or 'workspace'}.",
        'sourcePath': str(src),
        'versionKey': version_key(src.name),
    })
manifest.sort(key=lambda d: (d['folder'], d['name'].lower(), d['date']))
(repo/'manifest.json').write_text(json.dumps({'generatedAt': datetime.now().isoformat(), 'count': len(manifest), 'departments': folders, 'documents': manifest}, indent=2))

INDEX_HTML = '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>Rob\'s Document Vault 🦞</title>\n  <link rel="stylesheet" href="styles.css" />\n</head>\n<body>\n  <div id="lock" class="lock-screen">\n    <div class="lock-card">\n      <div class="lobster">🦞</div>\n      <h1>Rob\'s Document Vault</h1>\n      <p>Private document browser for Joe. Light password gate only.</p>\n      <form id="loginForm">\n        <input id="password" type="password" autocomplete="current-password" placeholder="Enter vault password" />\n        <button type="submit">Unlock Vault</button>\n      </form>\n      <p id="loginError" class="error"></p>\n      <p class="security-note">Note: this GitHub Pages version is for non-sensitive docs only.</p>\n    </div>\n  </div>\n\n  <div id="app" class="app hidden">\n    <header class="topbar">\n      <div>\n        <h1>Rob\'s Document Vault 🦞</h1>\n        <p id="subtitle">Loading documents...</p>\n      </div>\n      <button id="lockBtn" class="ghost">Lock</button>\n    </header>\n    <section class="controls">\n      <div class="search-wrap"><span>🔎</span><input id="search" type="search" placeholder="Search documents, departments, descriptions..." /></div>\n      <select id="sort"><option value="date-desc">Newest first</option><option value="date-asc">Oldest first</option><option value="name-asc">Name A-Z</option><option value="type-asc">Type</option></select>\n    </section>\n    <nav id="tabs" class="tabs"></nav>\n    <main><div id="summary" class="summary"></div><div id="cards" class="cards"></div><div id="empty" class="empty hidden">No documents match that search.</div></main>\n  </div>\n  <dialog id="historyDialog"><div class="dialog-head"><h2>Document History</h2><button id="closeHistory" class="ghost">Close</button></div><div id="historyBody"></div></dialog>\n  <script src="app.js"></script>\n</body>\n</html>\n'
STYLES_CSS = ':root{--bg:#0D1117;--panel:#161B22;--panel2:#1f2630;--border:#30363d;--text:#f0f6fc;--muted:#8b949e;--orange:#FF6B00;--gold:#C59E3C;--green:#3fb950;--red:#f85149}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top left,rgba(255,107,0,.16),transparent 35%),var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}.hidden{display:none!important}.lock-screen{min-height:100vh;display:grid;place-items:center;padding:24px}.lock-card{width:min(440px,100%);background:rgba(22,27,34,.94);border:1px solid var(--border);border-radius:24px;padding:28px;box-shadow:0 20px 60px rgba(0,0,0,.45);text-align:center}.lobster{font-size:52px}.lock-card h1{margin:8px 0;font-size:30px}.lock-card p{color:var(--muted)}form{display:grid;gap:12px;margin-top:18px}input,select,button{font:inherit}input,select{width:100%;border:1px solid var(--border);background:#0b1017;color:var(--text);border-radius:14px;padding:14px}button{border:0;border-radius:14px;padding:13px 16px;background:linear-gradient(135deg,#B03C00,#FF6B00);color:white;font-weight:800;cursor:pointer}.ghost{background:transparent;border:1px solid var(--border);color:var(--muted)}.error{color:var(--red);font-weight:700;min-height:20px}.security-note{font-size:12px}.app{max-width:1220px;margin:0 auto;padding:18px}.topbar{position:sticky;top:0;z-index:5;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 0;background:rgba(13,17,23,.9);backdrop-filter:blur(14px)}.topbar h1{margin:0;font-size:clamp(25px,5vw,42px)}.topbar p{margin:4px 0 0;color:var(--muted)}.controls{display:grid;grid-template-columns:1fr 190px;gap:12px;margin:10px 0 16px}.search-wrap{display:flex;align-items:center;gap:10px;background:var(--panel);border:1px solid var(--border);border-radius:16px;padding:0 12px}.search-wrap input{border:0;background:transparent}.tabs{display:flex;gap:8px;overflow-x:auto;padding:4px 0 14px}.tab{white-space:nowrap;background:var(--panel);border:1px solid var(--border);color:var(--muted);border-radius:999px;padding:10px 14px;font-weight:800}.tab.active{background:rgba(255,107,0,.15);border-color:var(--orange);color:var(--text)}.summary{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px}.stat{background:var(--panel);border:1px solid var(--border);border-radius:18px;padding:14px}.stat b{display:block;font-size:24px;color:var(--orange)}.stat span{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}.card{background:linear-gradient(180deg,var(--panel),rgba(22,27,34,.82));border:1px solid var(--border);border-radius:20px;padding:16px;display:flex;flex-direction:column;gap:12px;min-height:210px}.card:hover{border-color:rgba(255,107,0,.65)}.card-head{display:flex;gap:12px;align-items:flex-start}.icon{font-size:32px;width:46px;height:46px;display:grid;place-items:center;background:var(--panel2);border-radius:14px}.card h3{margin:0;font-size:17px;line-height:1.25}.meta{display:flex;flex-wrap:wrap;gap:7px;color:var(--muted);font-size:12px}.pill{border:1px solid var(--border);border-radius:999px;padding:4px 8px;background:#0b1017}.desc{color:var(--muted);font-size:13px;line-height:1.35;flex:1}.actions{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.view,.download,.history{display:block;text-align:center;text-decoration:none;border-radius:12px;padding:10px 12px;font-weight:800}.view{background:#0b1017;border:1px solid var(--border);color:var(--text)}.download{background:linear-gradient(135deg,#B03C00,#FF6B00);color:white}.history{background:#0b1017;border:1px solid var(--border);color:var(--muted)}.empty{text-align:center;color:var(--muted);padding:40px}dialog{width:min(760px,92vw);border:1px solid var(--border);border-radius:22px;background:var(--panel);color:var(--text);padding:0}dialog::backdrop{background:rgba(0,0,0,.72)}.dialog-head{display:flex;justify-content:space-between;align-items:center;padding:16px;border-bottom:1px solid var(--border)}.dialog-head h2{margin:0}#historyBody{padding:16px}.history-row{display:flex;justify-content:space-between;gap:12px;border:1px solid var(--border);border-radius:14px;padding:12px;margin-bottom:8px}.history-row a{color:var(--orange);font-weight:800}.history-actions{display:flex;align-items:center;gap:12px;flex-wrap:wrap;justify-content:flex-end;min-width:130px}@media(max-width:700px){.controls{grid-template-columns:1fr}.summary{grid-template-columns:repeat(2,1fr)}.cards{grid-template-columns:1fr}.topbar{align-items:flex-start}.actions{grid-template-columns:1fr}.app{padding:12px}.card{min-height:auto}.history-row{display:grid}.history-actions{justify-content:flex-start}}\n'
APP_JS = 'const VAULT_PASSWORD=\'soccer12\';\nconst VAULT_PUBLIC_BASE=\'https://roblobsterclaw.github.io/vault/\';\n\nconst state={\n  docs:[],\n  departments:{},\n  active:\'all\',\n  query:\'\',\n  sort:\'date-desc\'\n};\n\nconst $=id=>document.getElementById(id);\nconst iconFor=t=>({pdf:\'📕\',docx:\'📘\',xlsx:\'📗\'}[t]||\'📄\');\nconst fmtSize=b=>{\n  const u=[\'B\',\'KB\',\'MB\',\'GB\'];\n  let n=b,i=0;\n  while(n>1024&&i<u.length-1){n/=1024;i++}\n  return `${n.toFixed(n>9||i===0?0:1)} ${u[i]}`;\n};\n\nfunction isUnlocked(){\n  return sessionStorage.getItem(\'vaultUnlocked\')===\'yes\';\n}\n\nfunction showApp(){\n  $(\'lock\').classList.add(\'hidden\');\n  $(\'app\').classList.remove(\'hidden\');\n  loadManifest();\n}\n\nfunction showLock(){\n  sessionStorage.removeItem(\'vaultUnlocked\');\n  $(\'app\').classList.add(\'hidden\');\n  $(\'lock\').classList.remove(\'hidden\');\n}\n\n$(\'loginForm\').addEventListener(\'submit\',e=>{\n  e.preventDefault();\n  if($(\'password\').value.trim()===VAULT_PASSWORD){\n    sessionStorage.setItem(\'vaultUnlocked\',\'yes\');\n    showApp();\n  }else{\n    $(\'loginError\').textContent=\'Wrong password.\';\n  }\n});\n\n$(\'lockBtn\').addEventListener(\'click\',showLock);\n$(\'search\').addEventListener(\'input\',e=>{\n  state.query=e.target.value.toLowerCase();\n  render();\n});\n$(\'sort\').addEventListener(\'change\',e=>{\n  state.sort=e.target.value;\n  render();\n});\n$(\'closeHistory\').addEventListener(\'click\',()=>$(\'historyDialog\').close());\n\nasync function loadManifest(){\n  const res=await fetch(\'manifest.json\',{cache:\'no-store\'});\n  const data=await res.json();\n  state.docs=data.documents;\n  state.departments=data.departments;\n  $(\'subtitle\').textContent=`${data.count} documents • ${groupDocuments(data.documents).length} families • updated ${new Date(data.generatedAt).toLocaleString()}`;\n  renderTabs();\n  render();\n}\n\nfunction renderTabs(){\n  const tabs=$(\'tabs\');\n  const counts={all:groupDocuments(state.docs).length};\n  Object.keys(state.departments).forEach(k=>{\n    counts[k]=groupDocuments(state.docs.filter(d=>d.folder===k)).length;\n  });\n  tabs.innerHTML=\'\';\n  [[\'all\',\'All Documents\'],...Object.entries(state.departments)].forEach(([key,label])=>{\n    const b=document.createElement(\'button\');\n    b.className=`tab ${state.active===key?\'active\':\'\'}`;\n    b.textContent=`${label} (${counts[key]||0})`;\n    b.onclick=()=>{\n      state.active=key;\n      renderTabs();\n      render();\n    };\n    tabs.appendChild(b);\n  });\n}\n\nfunction filteredDocs(){\n  let docs=[...state.docs];\n  if(state.active!==\'all\')docs=docs.filter(d=>d.folder===state.active);\n  if(state.query){\n    docs=docs.filter(d=>searchText(d).includes(state.query));\n  }\n  return docs;\n}\n\nfunction searchText(doc){\n  return [\n    doc.name,\n    doc.department,\n    doc.description,\n    doc.type,\n    doc.fileName,\n    doc.versionKey,\n    familyKey(doc)\n  ].join(\' \').toLowerCase();\n}\n\nfunction groupDocuments(docs){\n  const groups=new Map();\n  docs.forEach(doc=>{\n    const key=familyKey(doc);\n    const group=groups.get(key)||{key,versions:[]};\n    group.versions.push(doc);\n    groups.set(key,group);\n  });\n\n  return [...groups.values()].map(group=>{\n    group.versions=sortVersions(group.versions);\n    group.doc=group.versions[0];\n    return group;\n  });\n}\n\nfunction familyKey(doc){\n  const seed=(doc.versionKey||doc.name||doc.fileName||\'\').toLowerCase();\n  const normalized=seed\n    .replace(/\\.[a-z0-9]+$/g,\' \')\n    .replace(/\\b20\\d{2}[-_ ]\\d{1,2}[-_ ]\\d{1,2}\\b/g,\' \')\n    .replace(/\\b\\d{1,2}[-_ ]\\d{1,2}[-_ ]\\d{2,4}\\b/g,\' \')\n    .replace(/\\b(v|version)\\s*\\d+(\\.\\d+)*\\b/g,\' \')\n    .replace(/\\b[a-f0-9]{8}\\b/g,\' \')\n    .replace(/\\b(updated|revised|clean|formatted|print|baseline|working|final|latest|from joe|joeedits|edits)\\b/g,\' \')\n    .replace(/[^a-z0-9]+/g,\' \')\n    .replace(/\\s+/g,\' \')\n    .trim();\n  return normalized||seed.trim()||doc.url;\n}\n\nfunction sortVersions(docs){\n  return [...docs].sort((a,b)=>\n    b.date.localeCompare(a.date)||\n    versionScore(b)-versionScore(a)||\n    b.name.localeCompare(a.name)||\n    b.type.localeCompare(a.type)\n  );\n}\n\nfunction versionScore(doc){\n  const text=[doc.name,doc.fileName,doc.versionKey].join(\' \');\n  const matches=[...text.matchAll(/\\bv(\\d+(?:\\.\\d+)*)\\b/gi)];\n  if(!matches.length)return 0;\n  return matches\n    .map(m=>m[1].split(\'.\').reduce((score,part)=>score*1000+Number(part),0))\n    .reduce((max,score)=>Math.max(max,score),0);\n}\n\nfunction sortedGroups(){\n  const groups=groupDocuments(filteredDocs()).map(group=>{\n    const versions=sortVersions(state.docs.filter(d=>familyKey(d)===group.key));\n    return {...group,versions,doc:versions[0]};\n  });\n  groups.sort((a,b)=>{\n    const docA=a.doc,docB=b.doc;\n    if(state.sort===\'date-asc\')return docA.date.localeCompare(docB.date)||docA.name.localeCompare(docB.name);\n    if(state.sort===\'name-asc\')return docA.name.localeCompare(docB.name);\n    if(state.sort===\'type-asc\')return docA.type.localeCompare(docB.type)||docA.name.localeCompare(docB.name);\n    return docB.date.localeCompare(docA.date)||docA.name.localeCompare(docB.name);\n  });\n  return groups;\n}\n\nfunction render(){\n  const groups=sortedGroups();\n  const familyCount=groupDocuments(state.docs).length;\n  $(\'summary\').innerHTML=`<div class="stat"><b>${groups.length}</b><span>Showing Families</span></div><div class="stat"><b>${familyCount}</b><span>Total Families</span></div><div class="stat"><b>${state.docs.length}</b><span>Total Docs</span></div><div class="stat"><b>${state.docs.filter(d=>d.type===\'pdf\').length}</b><span>PDFs</span></div>`;\n  $(\'empty\').classList.toggle(\'hidden\',groups.length>0);\n  $(\'cards\').innerHTML=\'\';\n  groups.forEach(group=>{\n    const doc=group.doc;\n    const versions=group.versions;\n    const card=document.createElement(\'article\');\n    card.className=\'card\';\n    card.innerHTML=`<div class="card-head"><div class="icon">${iconFor(doc.type)}</div><div><h3>${escapeHtml(doc.name)}</h3><div class="meta"><span class="pill">${escapeHtml(doc.department)}</span><span class="pill">${doc.date}</span><span class="pill">${doc.type.toUpperCase()} • ${fmtSize(doc.size)}</span><span class="pill">${versions.length} version${versions.length===1?\'\':\'s\'}</span></div></div></div><p class="desc">${escapeHtml(doc.description)}</p><div class="actions"><a class="view" href="${escapeAttr(viewUrl(doc))}" target="_blank" rel="noopener">View</a><a class="download" href="${encodeURI(doc.url)}" download>Download</a><button class="history" data-key="${escapeAttr(group.key)}">History (${versions.length})</button></div>`;\n    card.querySelector(\'.history\').onclick=()=>showHistory(group.key);\n    $(\'cards\').appendChild(card);\n  });\n}\n\nfunction showHistory(key){\n  const versions=sortVersions(state.docs.filter(d=>familyKey(d)===key));\n  $(\'historyBody\').innerHTML=versions.map(v=>`<div class="history-row"><div><strong>${escapeHtml(v.name)}</strong><div class="meta">${v.date} • ${escapeHtml(v.department)} • ${v.type.toUpperCase()} • ${fmtSize(v.size)}</div></div><div class="history-actions"><a href="${escapeAttr(viewUrl(v))}" target="_blank" rel="noopener">View</a><a href="${encodeURI(v.url)}" download>Download</a></div></div>`).join(\'\')||\'<p>No older versions found.</p>\';\n  $(\'historyDialog\').showModal();\n}\n\nfunction publicDocUrl(doc){\n  return new URL(encodeURI(doc.url),VAULT_PUBLIC_BASE).href;\n}\n\nfunction viewUrl(doc){\n  if(doc.type===\'pdf\')return encodeURI(doc.url);\n  if(doc.type===\'docx\'||doc.type===\'xlsx\'){\n    return `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(publicDocUrl(doc))}`;\n  }\n  return encodeURI(doc.url);\n}\n\nfunction escapeHtml(s){\n  return String(s).replace(/[&<>"\']/g,m=>({\'&\':\'&amp;\',\'<\':\'&lt;\',\'>\':\'&gt;\',\'"\':\'&quot;\',"\'":\'&#39;\'}[m]));\n}\n\nfunction escapeAttr(s){\n  return escapeHtml(s).replace(/`/g,\'&#96;\');\n}\n\nif(isUnlocked())showApp();\n'
TEST_VAULT = 'import json\nimport re\nfrom pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n\ndef test_manifest_has_required_shape_and_files_exist():\n    data = json.loads((ROOT / \'manifest.json\').read_text())\n    assert data[\'count\'] == len(data[\'documents\'])\n    assert data[\'count\'] > 0\n    required = {\'name\', \'folder\', \'date\', \'description\', \'url\', \'type\', \'versionKey\'}\n    for doc in data[\'documents\']:\n        assert required.issubset(doc)\n        assert (ROOT / doc[\'url\']).exists(), doc[\'url\']\n        assert doc[\'folder\'] in data[\'departments\']\n        assert doc[\'type\'] in {\'docx\', \'pdf\', \'xlsx\'}\n\ndef test_app_contains_core_features():\n    html = (ROOT / \'index.html\').read_text()\n    js = (ROOT / \'app.js\').read_text()\n    css = (ROOT / \'styles.css\').read_text()\n    assert "Rob\'s Document Vault" in html\n    assert \'manifest.json\' in js\n    assert \'History\' in js\n    assert \'groupDocuments\' in js\n    assert \'familyKey\' in js\n    assert \'Showing Families\' in js\n    assert \'VAULT_PUBLIC_BASE\' in js\n    assert \'view.officeapps.live.com\' in js\n    assert \'target="_blank"\' in js\n    assert \'sessionStorage\' in js\n    assert "VAULT_PASSWORD=\'soccer12\'" in js\n    assert \'ROBLOBSTER\' not in js\n    assert \'.view\' in css\n    assert \'@media(max-width:700px)\' in css\n\ndef test_department_folders_exist():\n    expected = [\'tuckerton-group\',\'investing\',\'rebolt\',\'firehouse\',\'real-estate\',\'family\',\'lobster-press\',\'research\',\'daily-rundowns\']\n    for folder in expected:\n        assert (ROOT / \'docs\' / folder).is_dir()\n\ndef test_manifest_has_collapsible_document_families():\n    data = json.loads((ROOT / \'manifest.json\').read_text())\n    family_counts = {}\n    for doc in data[\'documents\']:\n        key = family_key(doc)\n        family_counts[key] = family_counts.get(key, 0) + 1\n\n    assert len(family_counts) < data[\'count\']\n    assert family_counts[\'jfl ttd\'] >= 50\n    assert family_counts[\'morning joes rundown\'] >= 20\n    assert family_counts[\'mission control\'] >= 10\n    assert family_counts[\'morning package\'] >= 5\n\ndef family_key(doc):\n    seed = (doc.get(\'versionKey\') or doc.get(\'name\') or doc.get(\'fileName\') or \'\').lower()\n    normalized = re.sub(r\'\\.[a-z0-9]+$\', \' \', seed)\n    normalized = re.sub(r\'\\b20\\d{2}[-_ ]\\d{1,2}[-_ ]\\d{1,2}\\b\', \' \', normalized)\n    normalized = re.sub(r\'\\b\\d{1,2}[-_ ]\\d{1,2}[-_ ]\\d{2,4}\\b\', \' \', normalized)\n    normalized = re.sub(r\'\\b(v|version)\\s*\\d+(\\.\\d+)*\\b\', \' \', normalized)\n    normalized = re.sub(r\'\\b[a-f0-9]{8}\\b\', \' \', normalized)\n    normalized = re.sub(\n        r\'\\b(updated|revised|clean|formatted|print|baseline|working|final|latest|from joe|joeedits|edits)\\b\',\n        \' \',\n        normalized,\n    )\n    normalized = re.sub(r\'[^a-z0-9]+\', \' \', normalized)\n    normalized = re.sub(r\'\\s+\', \' \', normalized).strip()\n    return normalized or seed.strip() or doc[\'url\']\n'
README_MD = "# Rob's Document Vault 🦞\n\nStatic GitHub Pages document portal for Joe.\n\n- URL target: https://roblobsterclaw.github.io/vault/\n- Light password gate: `soccer12`\n- Documents: 291 files copied from the last 60 days\n- Note: GitHub Pages is public hosting. This version is for non-sensitive docs until upgraded to Cloudflare Access or another real auth layer.\n"

(repo/'index.html').write_text(INDEX_HTML)
(repo/'styles.css').write_text(STYLES_CSS)
(repo/'app.js').write_text(APP_JS)
(repo/'README.md').write_text(README_MD.replace('291 files', f'{len(manifest)} files'))
(repo/'.nojekyll').write_text('')
(repo/'tests').mkdir(exist_ok=True)
(repo/'tests'/'test_vault.py').write_text(TEST_VAULT)
print(json.dumps({'repo': str(repo), 'documents': len(manifest), 'folders': {k: sum(1 for d in manifest if d['folder']==k) for k in folders}}, indent=2))
