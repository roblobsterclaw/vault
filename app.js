const VAULT_PASSWORD='soccer12';
const VAULT_PUBLIC_BASE='https://roblobsterclaw.github.io/vault/';

const state={
  docs:[],
  departments:{},
  active:'all',
  query:'',
  sort:'date-desc'
};

const $=id=>document.getElementById(id);
const iconFor=t=>({pdf:'📕',docx:'📘',xlsx:'📗'}[t]||'📄');
const fmtSize=b=>{
  const u=['B','KB','MB','GB'];
  let n=b,i=0;
  while(n>1024&&i<u.length-1){n/=1024;i++}
  return `${n.toFixed(n>9||i===0?0:1)} ${u[i]}`;
};

function isUnlocked(){
  return sessionStorage.getItem('vaultUnlocked')==='yes';
}

function showApp(){
  $('lock').classList.add('hidden');
  $('app').classList.remove('hidden');
  loadManifest();
}

function showLock(){
  sessionStorage.removeItem('vaultUnlocked');
  $('app').classList.add('hidden');
  $('lock').classList.remove('hidden');
}

$('loginForm').addEventListener('submit',e=>{
  e.preventDefault();
  if($('password').value.trim()===VAULT_PASSWORD){
    sessionStorage.setItem('vaultUnlocked','yes');
    showApp();
  }else{
    $('loginError').textContent='Wrong password.';
  }
});

$('lockBtn').addEventListener('click',showLock);
$('search').addEventListener('input',e=>{
  state.query=e.target.value.toLowerCase();
  render();
});
$('sort').addEventListener('change',e=>{
  state.sort=e.target.value;
  render();
});
$('closeHistory').addEventListener('click',()=>$('historyDialog').close());

async function loadManifest(){
  const res=await fetch('manifest.json',{cache:'no-store'});
  const data=await res.json();
  state.docs=data.documents;
  state.departments=data.departments;
  $('subtitle').textContent=`${data.count} documents • ${groupDocuments(data.documents).length} families • updated ${new Date(data.generatedAt).toLocaleString()}`;
  renderTabs();
  render();
}

function renderTabs(){
  const tabs=$('tabs');
  const counts={all:groupDocuments(state.docs).length};
  Object.keys(state.departments).forEach(k=>{
    counts[k]=groupDocuments(state.docs.filter(d=>d.folder===k)).length;
  });
  tabs.innerHTML='';
  [['all','All Documents'],...Object.entries(state.departments)].forEach(([key,label])=>{
    const b=document.createElement('button');
    b.className=`tab ${state.active===key?'active':''}`;
    b.textContent=`${label} (${counts[key]||0})`;
    b.onclick=()=>{
      state.active=key;
      renderTabs();
      render();
    };
    tabs.appendChild(b);
  });
}

function filteredDocs(){
  let docs=[...state.docs];
  if(state.active!=='all')docs=docs.filter(d=>d.folder===state.active);
  if(state.query){
    docs=docs.filter(d=>searchText(d).includes(state.query));
  }
  return docs;
}

function searchText(doc){
  return [
    doc.name,
    doc.department,
    doc.description,
    doc.type,
    doc.fileName,
    doc.versionKey,
    familyKey(doc)
  ].join(' ').toLowerCase();
}

function groupDocuments(docs){
  const groups=new Map();
  docs.forEach(doc=>{
    const key=familyKey(doc);
    const group=groups.get(key)||{key,versions:[]};
    group.versions.push(doc);
    groups.set(key,group);
  });

  return [...groups.values()].map(group=>{
    group.versions=sortVersions(group.versions);
    group.doc=group.versions[0];
    return group;
  });
}

function familyKey(doc){
  const seed=(doc.versionKey||doc.name||doc.fileName||'').toLowerCase();
  const normalized=seed
    .replace(/\.[a-z0-9]+$/g,' ')
    .replace(/\b20\d{2}[-_ ]\d{1,2}[-_ ]\d{1,2}\b/g,' ')
    .replace(/\b\d{1,2}[-_ ]\d{1,2}[-_ ]\d{2,4}\b/g,' ')
    .replace(/\b(v|version)\s*\d+(\.\d+)*\b/g,' ')
    .replace(/\b[a-f0-9]{8}\b/g,' ')
    .replace(/\b(updated|revised|clean|formatted|print|baseline|working|final|latest|from joe|joeedits|edits)\b/g,' ')
    .replace(/[^a-z0-9]+/g,' ')
    .replace(/\s+/g,' ')
    .trim();
  return normalized||seed.trim()||doc.url;
}

function sortVersions(docs){
  return [...docs].sort((a,b)=>
    b.date.localeCompare(a.date)||
    versionScore(b)-versionScore(a)||
    b.name.localeCompare(a.name)||
    b.type.localeCompare(a.type)
  );
}

function versionScore(doc){
  const text=[doc.name,doc.fileName,doc.versionKey].join(' ');
  const matches=[...text.matchAll(/\bv(\d+(?:\.\d+)*)\b/gi)];
  if(!matches.length)return 0;
  return matches
    .map(m=>m[1].split('.').reduce((score,part)=>score*1000+Number(part),0))
    .reduce((max,score)=>Math.max(max,score),0);
}

function sortedGroups(){
  const groups=groupDocuments(filteredDocs()).map(group=>{
    const versions=sortVersions(state.docs.filter(d=>familyKey(d)===group.key));
    return {...group,versions,doc:versions[0]};
  });
  groups.sort((a,b)=>{
    const docA=a.doc,docB=b.doc;
    if(state.sort==='date-asc')return docA.date.localeCompare(docB.date)||docA.name.localeCompare(docB.name);
    if(state.sort==='name-asc')return docA.name.localeCompare(docB.name);
    if(state.sort==='type-asc')return docA.type.localeCompare(docB.type)||docA.name.localeCompare(docB.name);
    return docB.date.localeCompare(docA.date)||docA.name.localeCompare(docB.name);
  });
  return groups;
}

function render(){
  const groups=sortedGroups();
  const familyCount=groupDocuments(state.docs).length;
  $('summary').innerHTML=`<div class="stat"><b>${groups.length}</b><span>Showing Families</span></div><div class="stat"><b>${familyCount}</b><span>Total Families</span></div><div class="stat"><b>${state.docs.length}</b><span>Total Docs</span></div><div class="stat"><b>${state.docs.filter(d=>d.type==='pdf').length}</b><span>PDFs</span></div>`;
  $('empty').classList.toggle('hidden',groups.length>0);
  $('cards').innerHTML='';
  groups.forEach(group=>{
    const doc=group.doc;
    const versions=group.versions;
    const card=document.createElement('article');
    card.className='card';
    card.innerHTML=`<div class="card-head"><div class="icon">${iconFor(doc.type)}</div><div><h3>${escapeHtml(doc.name)}</h3><div class="meta"><span class="pill">${escapeHtml(doc.department)}</span><span class="pill">${doc.date}</span><span class="pill">${doc.type.toUpperCase()} • ${fmtSize(doc.size)}</span><span class="pill">${versions.length} version${versions.length===1?'':'s'}</span></div></div></div><p class="desc">${escapeHtml(doc.description)}</p><div class="actions"><a class="view" href="${escapeAttr(viewUrl(doc))}" target="_blank" rel="noopener">View</a><a class="download" href="${encodeURI(doc.url)}" download>Download</a><button class="history" data-key="${escapeAttr(group.key)}">History (${versions.length})</button></div>`;
    card.querySelector('.history').onclick=()=>showHistory(group.key);
    $('cards').appendChild(card);
  });
}

function showHistory(key){
  const versions=sortVersions(state.docs.filter(d=>familyKey(d)===key));
  $('historyBody').innerHTML=versions.map(v=>`<div class="history-row"><div><strong>${escapeHtml(v.name)}</strong><div class="meta">${v.date} • ${escapeHtml(v.department)} • ${v.type.toUpperCase()} • ${fmtSize(v.size)}</div></div><div class="history-actions"><a href="${escapeAttr(viewUrl(v))}" target="_blank" rel="noopener">View</a><a href="${encodeURI(v.url)}" download>Download</a></div></div>`).join('')||'<p>No older versions found.</p>';
  $('historyDialog').showModal();
}

function publicDocUrl(doc){
  return new URL(encodeURI(doc.url),VAULT_PUBLIC_BASE).href;
}

function viewUrl(doc){
  if(doc.type==='pdf')return encodeURI(doc.url);
  if(doc.type==='docx'||doc.type==='xlsx'){
    return `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(publicDocUrl(doc))}`;
  }
  return encodeURI(doc.url);
}

function escapeHtml(s){
  return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

function escapeAttr(s){
  return escapeHtml(s).replace(/`/g,'&#96;');
}

if(isUnlocked())showApp();
