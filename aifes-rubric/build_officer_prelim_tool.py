# -*- coding: utf-8 -*-
"""
役員予備審査ツール（HTML・独立版）を生成する。

- 役員4名に1人1ファイルずつ個別配布する採点ページ（officer_prelim_日名.html）
- 集計係が4名分の結果ファイルを読み込んで1〜4位を集計するページ（officer_prelim_集計.html）

Excel「04_役員予備審査投票」シートとは完全に独立（2026-08-27 ユーザー合意）。
データは officer_prelim_data.py（OFFICERS / GF_ENTRIES）が唯一の定義元。
役員は点数をつけない。AI予備審査（rubric_data.py）の結果を参考値として見た上で、
1〜4位を選び、理由を書くだけ。Copilot連携・審査員別ペルソナ文書は用意しない。
"""
import html
import json

from rubric_data import CRITERIA
from officer_prelim_data import OFFICERS, GF_ENTRIES, ai_total, ai_band

CID_COLOR = {
    "C1": ("#C13A22", "#FCEAE6"),
    "C2": ("#07756B", "#E1F4F1"),
    "C3": ("#6244C9", "#EDE9FB"),
    "C4": ("#A15900", "#FBEEDC"),
    "C5": ("#B93077", "#FBE9F2"),
    "C6": ("#155FAF", "#E4EFFB"),
}


def E(s):
    return html.escape(str(s), quote=True)


def js_embed(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def entries_payload():
    out = []
    for e in GF_ENTRIES:
        crits = []
        for c in CRITERIA:
            lv = e["levels"].get(c["id"], 0)
            level_text = c["levels"][5 - lv] if lv else "（未評価）"
            color, color_s = CID_COLOR[c["id"]]
            crits.append(dict(
                id=c["id"], name=c["name"], weight=c["weight"], level=lv,
                levelText=level_text, color=color, colorS=color_s,
            ))
        total = ai_total(e)
        out.append(dict(
            code=e["code"], dept=e["dept"], title=e["title"], submitter=e["submitter"],
            primary=e["primary"], procedure=e["procedure"], gaps=e["gaps"],
            aiNote=e["ai_note"], criteria=crits, aiTotal=total, aiBand=ai_band(total),
        ))
    return out


CSS = """
:root{
  --bg:#fafbfc; --panel:#fff; --line:#e3e6ee; --ink:#1c2233; --mute:#707890;
  --accent:#1f3a5f; --accent2:#3a6ea5; --ok:#1f7a4d; --ok-s:#e6f5ec;
  --warn:#a15900; --warn-s:#fbeedc; --bad:#c2372b; --bad-s:#fbeae8;
  --radius:12px;
}
*{box-sizing:border-box}
body{margin:0;font-family:"Meiryo","游ゴシック","Yu Gothic","Hiragino Kaku Gothic ProN",sans-serif;background:var(--bg);color:var(--ink);line-height:1.7}
header.top{position:sticky;top:0;z-index:20;background:linear-gradient(120deg,var(--accent),var(--accent2));color:#fff;padding:16px 24px;display:flex;align-items:center;gap:20px;box-shadow:0 4px 14px rgba(31,58,95,.25)}
header.top h1{font-size:16px;margin:0;font-weight:700}
header.top .who{font-size:13px;opacity:.9}
header.top .stats{margin-left:auto;display:flex;gap:16px;align-items:center;font-size:13px}
header.top .stats b{font-size:16px;font-weight:800}
header.top button{background:#fff;color:var(--accent);border:0;border-radius:8px;padding:9px 16px;font-weight:700;font-size:13px;cursor:pointer}
header.top button:hover{opacity:.9}
header.top label.imp{background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.5);border-radius:8px;padding:9px 14px;font-size:12px;cursor:pointer}
.wrap{display:flex;max-width:1320px;margin:0 auto;gap:20px;padding:20px 24px 80px;align-items:flex-start}
.list{width:300px;flex:none;position:sticky;top:74px}
.list .card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:6px;max-height:calc(100vh - 100px);overflow:auto}
.row{display:block;width:100%;text-align:left;border:0;background:none;padding:12px 12px;border-radius:9px;cursor:pointer;margin-bottom:2px}
.row:hover{background:#f2f4f8}
.row.sel{background:#eaf0fb;box-shadow:inset 0 0 0 1.5px var(--accent2)}
.row .t{font-size:13px;font-weight:700;color:var(--ink);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.row .m{display:flex;justify-content:space-between;align-items:center;margin-top:6px;font-size:11px;color:var(--mute)}
.row .badge{font-weight:700;border-radius:6px;padding:2px 7px;font-size:11px}
.row .rankchip{background:var(--accent);color:#fff;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:700}
.detail{flex:1;min-width:0;background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:28px 32px}
.eyebrow{font-size:12px;color:var(--mute);letter-spacing:.5px}
.detail h2{font-size:24px;margin:6px 0 2px;color:var(--ink)}
.meta{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--mute);margin-bottom:18px}
.gapwarn{background:var(--warn-s);border:1px solid #f0d19a;color:var(--warn);border-radius:9px;padding:12px 16px;font-size:13px;margin:14px 0}
section.panel{margin:22px 0;padding:20px 22px;border:1px solid var(--line);border-radius:var(--radius);background:#fcfcfe}
section.panel h3{margin:0 0 12px;font-size:14px;color:var(--accent)}
.ainote{background:#f2f7fc;border-left:4px solid var(--accent2);border-radius:8px;padding:12px 16px;font-size:13px;color:#25354a;margin-bottom:14px}
table.ax{width:100%;border-collapse:collapse;font-size:13px}
table.ax td{padding:9px 6px;border-bottom:1px solid var(--line);vertical-align:top}
table.ax td.name{width:34%;font-weight:700}
table.ax td.name span{display:block;font-weight:400;color:var(--mute);font-size:11px;margin-top:2px}
table.ax td.lv{width:14%;text-align:center;font-weight:800;font-size:15px}
table.ax td.txt{color:#333;font-size:12.5px}
.bar{height:6px;border-radius:4px;background:#eef0f6;overflow:hidden;margin-top:5px}
.bar i{display:block;height:100%}
.totalrow{display:flex;align-items:baseline;gap:10px;margin-top:14px}
.totalrow .num{font-size:30px;font-weight:800;color:var(--accent)}
.totalrow .band{font-size:13px;font-weight:800;border-radius:7px;padding:3px 10px}
.band-S{background:#e6f5ec;color:#1f7a4d}
.band-A{background:#e4effb;color:#155faf}
.band-B{background:#fbeedc;color:#a15900}
.band-C{background:#fbeae8;color:#c2372b}
.links{font-size:13px;color:#333}
.links dt{font-weight:700;color:var(--mute);font-size:11px;margin-top:8px}
.links dd{margin:2px 0 0}
.rankbtns{display:flex;gap:10px;flex-wrap:wrap}
.rankbtns button{flex:1;min-width:110px;border:1.5px solid var(--accent2);background:#fff;color:var(--accent2);border-radius:9px;padding:12px 10px;font-weight:700;font-size:13px;cursor:pointer}
.rankbtns button.on{background:var(--accent2);color:#fff}
.rankbtns button:hover{opacity:.88}
.rankhint{font-size:12px;color:var(--mute);margin-top:10px}
textarea{width:100%;border:1.5px solid var(--line);border-radius:9px;padding:10px 12px;font-size:13px;font-family:inherit;resize:vertical;box-sizing:border-box}
.nav{display:flex;justify-content:space-between;margin-top:22px}
.nav button{border:1.5px solid var(--line);background:#fff;border-radius:9px;padding:9px 16px;font-size:13px;cursor:pointer}
.nav button:disabled{opacity:.35;cursor:default}
.savebar{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid var(--line);padding:8px 24px;font-size:12px;color:var(--mute);display:flex;gap:10px;align-items:center}
.savebar .dot{width:8px;height:8px;border-radius:50%;background:var(--ok)}
.savebar .dot.off{background:var(--bad)}
.progress{display:flex;gap:8px;font-size:12px;color:var(--mute);align-items:center;margin:6px 0 0}
.progress .step{display:flex;align-items:center;gap:5px}
.progress .dot2{width:16px;height:16px;border-radius:50%;background:#eee;color:#aaa;display:inline-flex;align-items:center;justify-content:center;font-size:10px;font-weight:800}
.progress .step.ok .dot2{background:var(--ok);color:#fff}
"""

JS_TEMPLATE = r"""
const OFFICER = __OFFICER__;
const ENTRIES = __ENTRIES__;
const STORE_KEY = 'aifes2026_officer_prelim_' + OFFICER.key;

let state = {};
let sel = 0;
let canPersist = false;

function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function rec(code){ if(!state[code]) state[code] = {rank:'', reason:''}; return state[code]; }

function loadLocal(){
  try{
    const raw = localStorage.getItem(STORE_KEY);
    canPersist = true;
    if(raw){ state = JSON.parse(raw).state || {}; }
  }catch(e){ canPersist = false; }
}
function saveLocal(){
  if(!canPersist) return;
  try{ localStorage.setItem(STORE_KEY, JSON.stringify({state, at:new Date().toISOString()})); }catch(e){ canPersist = false; }
  paintSave();
}
function paintSave(){
  const dot = document.getElementById('saveDot'), txt = document.getElementById('saveTxt');
  if(!dot) return;
  if(canPersist){ dot.className='dot'; txt.textContent='自動保存 有効（このPC・このブラウザのみ）。作業が終わったら必ず上の「結果をエクスポート」でファイルを書き出してください。'; }
  else{ dot.className='dot off'; txt.textContent='自動保存 無効。こまめに「結果をエクスポート」でファイルを書き出してください。'; }
}

// 同じ順位を別の作品につけたら、元の作品からは自動的に外す（重複防止）
function setRank(code, rank){
  const r = rec(code);
  if(String(r.rank) === String(rank)){ r.rank = ''; touch(); return; }
  ENTRIES.forEach(e=>{ if(e.code!==code && String(rec(e.code).rank)===String(rank)) rec(e.code).rank=''; });
  r.rank = String(rank);
  touch();
}
function touch(){ saveLocal(); renderAll(); }

function bandClass(b){ return 'band-' + (b||'C'); }

function renderList(){
  const box = document.getElementById('rows');
  const a = ENTRIES.slice().sort((x,y)=> y.aiTotal - x.aiTotal);
  box.innerHTML = a.map(e=>{
    const i = ENTRIES.indexOf(e);
    const r = rec(e.code);
    return `<button class="row ${i===sel?'sel':''}" data-i="${i}">
      <div class="t">${esc(e.dept)}</div>
      <div class="m">
        <span class="badge ${bandClass(e.aiBand)}" style="background:transparent;color:inherit">AI ${e.aiTotal}点・${esc(e.aiBand)}</span>
        ${r.rank ? `<span class="rankchip">${r.rank}位</span>` : ''}
      </div>
    </button>`;
  }).join('');
  box.querySelectorAll('.row').forEach(el=> el.onclick = ()=>{ sel = +el.dataset.i; renderAll(); window.scrollTo(0,0); });

  const done = ENTRIES.filter(e=>rec(e.code).rank).length;
  document.getElementById('hDone').innerHTML = `<b>${done}</b>/${ENTRIES.length}位づけ済み`;
}

function renderDetail(){
  const e = ENTRIES[sel], r = rec(e.code);
  const ax = e.criteria.map(c=>`
    <tr>
      <td class="name">${esc(c.name)}<span>配点 ${c.weight}点</span></td>
      <td class="lv" style="color:${c.color}">${c.level || '—'}<div class="bar"><i style="width:${c.level? c.level/5*100:0}%;background:${c.color}"></i></div></td>
      <td class="txt">${esc(c.levelText)}</td>
    </tr>`).join('');

  document.getElementById('detail').innerHTML = `
    <div class="eyebrow">${esc(e.code)}</div>
    <h2>${esc(e.dept)}</h2>
    <div class="meta"><span>${esc(e.title)}</span><span>提出者：${esc(e.submitter)}</span></div>

    <div class="progress">
      ${[['1〜4位を選ぶ', !!r.rank],['理由を書く', !!r.reason.trim()]].map(([lab,ok])=>
        `<span class="step ${ok?'ok':''}"><span class="dot2">${ok?'✓':'-'}</span>${lab}</span>`).join('')}
    </div>

    ${e.gaps.length ? `<div class="gapwarn"><b>提出物の不足</b>：${e.gaps.map(esc).join(' / ')}</div>` : ''}

    <section class="panel">
      <h3>AI予備審査（参考値・編集不可）</h3>
      ${e.aiNote ? `<div class="ainote">${esc(e.aiNote)}</div>` : ''}
      <table class="ax">${ax}</table>
      <div class="totalrow">
        <span class="num">${e.aiTotal}</span><span style="color:#888;font-size:13px">/ 100点</span>
        <span class="band ${bandClass(e.aiBand)}">${esc(e.aiBand)}ランク</span>
      </div>
    </section>

    <section class="panel">
      <h3>提出物</h3>
      <dl class="links">
        <dt>作品</dt><dd>${esc(e.primary || '未登録')}</dd>
        <dt>手順書・補足資料</dt><dd>${esc(e.procedure || '未登録')}</dd>
      </dl>
    </section>

    <section class="panel">
      <h3>STEP 1：1〜4位を選ぶ</h3>
      <div class="rankbtns">
        ${[1,2,3,4].map(n=>`<button class="${String(r.rank)===String(n)?'on':''}" data-rank="${n}">${n}位に選ぶ</button>`).join('')}
      </div>
      <div class="rankhint">${r.rank ? `<b>${r.rank}位</b>に選んでいます。もう一度押すと解除できます。同じ順位を他の部門につけると、こちらの順位は自動で外れます。` : '決勝に進めたい順に、1位から選んでください。選ばない部門はそのままで構いません。'}</div>
    </section>

    <section class="panel">
      <h3>STEP 2：理由を書く（任意・集計係が参照します）</h3>
      <textarea id="fReason" rows="3" placeholder="例）AIの点数以上に、部門全体を巻き込んだ広がり方に説得力がある。">${esc(r.reason)}</textarea>
    </section>

    <div class="nav">
      <button id="prev" ${sel===0?'disabled':''}>← 前の部門</button>
      <button id="next" ${sel===ENTRIES.length-1?'disabled':''}>次の部門 →</button>
    </div>`;

  document.querySelectorAll('[data-rank]').forEach(b=> b.onclick = ()=> setRank(e.code, b.dataset.rank));
  const ta = document.getElementById('fReason');
  if(ta) ta.oninput = ()=>{ r.reason = ta.value; saveLocal(); };
  document.getElementById('prev').onclick = ()=>{ if(sel>0){ sel--; renderAll(); window.scrollTo(0,0); } };
  document.getElementById('next').onclick = ()=>{ if(sel<ENTRIES.length-1){ sel++; renderAll(); window.scrollTo(0,0); } };
}

function renderAll(){ renderList(); renderDetail(); }

function doExport(){
  const payload = {
    officer: OFFICER, exportedAt: new Date().toISOString(),
    ranks: ENTRIES.map(e=>({code:e.code, dept:e.dept, rank: rec(e.code).rank || null, reason: rec(e.code).reason || ''})),
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `予備審査_${OFFICER.name}_結果.json`;
  document.body.appendChild(a); a.click(); a.remove();
}
function doImport(file){
  const reader = new FileReader();
  reader.onload = ()=>{
    try{
      const data = JSON.parse(reader.result);
      (data.ranks||[]).forEach(x=>{ if(ENTRIES.some(e=>e.code===x.code)) state[x.code] = {rank:x.rank||'', reason:x.reason||''}; });
      touch();
    }catch(e){ alert('読み込みに失敗しました。正しいJSONファイルか確認してください。'); }
  };
  reader.readAsText(file);
}

loadLocal();
document.getElementById('exportBtn').onclick = doExport;
document.getElementById('importInput').onchange = (ev)=>{ if(ev.target.files[0]) doImport(ev.target.files[0]); };
paintSave();
renderAll();
"""


def render_officer_html(officer):
    entries = entries_payload()
    body = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<title>AIFES 2026 グランドフィナーレ 役員予備審査 — {E(officer['name'])}</title>
<style>{CSS}</style></head>
<body>
<header class="top">
  <div>
    <h1>AIFES 2026 グランドフィナーレ・役員予備審査</h1>
    <div class="who">{E(officer['name'])} さん専用ページ</div>
  </div>
  <div class="stats">
    <span id="hDone"><b>0</b>/{len(entries)}位づけ済み</span>
  </div>
  <label class="imp">結果を読み込む<input id="importInput" type="file" accept="application/json" style="display:none"></label>
  <button id="exportBtn">結果をエクスポート</button>
</header>
<div class="wrap">
  <div class="list"><div class="card" id="rows"></div></div>
  <div class="detail" id="detail"></div>
</div>
<div class="savebar"><span class="dot" id="saveDot"></span><span id="saveTxt"></span></div>
<script>
{JS_TEMPLATE.replace('__OFFICER__', js_embed(officer)).replace('__ENTRIES__', js_embed(entries))}
</script>
</body></html>"""
    return body


TALLY_CSS = CSS + """
table.tally{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}
table.tally th,table.tally td{border-bottom:1px solid var(--line);padding:10px 8px;text-align:left}
table.tally th{color:var(--mute);font-weight:700;font-size:11px}
table.tally td.num{text-align:center;font-weight:700}
tr.advance{background:#e6f5ec}
.upload-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:16px 0}
.upload-grid .slot{border:1.5px dashed var(--line);border-radius:10px;padding:16px;text-align:center;font-size:12.5px}
.upload-grid .slot.done{border-color:var(--ok);background:var(--ok-s)}
.upload-grid .slot input{display:block;margin:10px auto 0}
"""

TALLY_JS = r"""
const OFFICERS = __OFFICERS__;
const ENTRIES = __ENTRIES__;
let ballots = {}; // officerKey -> {code:rank}
let reasons = {}; // officerKey -> {code:reason}

function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

function renderSlots(){
  document.getElementById('slots').innerHTML = OFFICERS.map(o=>{
    const got = !!ballots[o.key];
    return `<div class="slot ${got?'done':''}">
      <b>${esc(o.name)}</b><br>${got? '✓ 読み込み済み' : '未読み込み'}
      <input type="file" accept="application/json" data-key="${o.key}">
    </div>`;
  }).join('');
  document.querySelectorAll('[data-key]').forEach(inp=>{
    inp.onchange = (ev)=>{
      const f = ev.target.files[0]; if(!f) return;
      const reader = new FileReader();
      reader.onload = ()=>{
        try{
          const data = JSON.parse(reader.result);
          const map = {}, rmap = {};
          (data.ranks||[]).forEach(x=>{ if(x.rank) map[x.code]=String(x.rank); rmap[x.code]=x.reason||''; });
          ballots[inp.dataset.key] = map;
          reasons[inp.dataset.key] = rmap;
          renderAll();
        }catch(e){ alert('読み込みに失敗しました。'); }
      };
      reader.readAsText(f);
    };
  });
}

function computeTally(){
  const rows = ENTRIES.map(e=>{
    let c1=0,c2=0,c3=0,c4=0;
    Object.values(ballots).forEach(map=>{
      const r = map[e.code];
      if(r==='1') c1++; else if(r==='2') c2++; else if(r==='3') c3++; else if(r==='4') c4++;
    });
    const total = c1*10 + c2*8 + c3*7 + c4*6;
    const protected_ = c1 >= 1;
    const key = (protected_?100000:0) + total*100 + c1*10 + c2;
    return {e, c1,c2,c3,c4, total, protected_, key};
  });
  const n = Object.keys(ballots).length;
  rows.sort((a,b)=> b.key - a.key);
  rows.forEach((r,i)=> r.finalRank = i+1);
  return {rows, n};
}

function renderAll(){
  renderSlots();
  const {rows, n} = computeTally();
  const submitted = Object.keys(ballots).length;
  document.getElementById('nSubmitted').textContent = submitted;
  const enough = submitted >= 4;
  document.getElementById('note').style.display = enough ? 'none' : 'block';
  document.getElementById('tallyBody').innerHTML = rows.map(r=>`
    <tr class="${enough && r.finalRank<=4 ? 'advance' : ''}">
      <td class="num">${enough ? r.finalRank : '—'}</td>
      <td>${esc(r.e.dept)}<div style="color:#888;font-size:11px">${esc(r.e.title)}</div></td>
      <td class="num">${r.c1}</td><td class="num">${r.c2}</td><td class="num">${r.c3}</td><td class="num">${r.c4}</td>
      <td class="num">${r.total}</td>
      <td class="num">${r.protected_ ? '◎' : ''}</td>
      <td class="num">AI ${r.e.aiTotal}点・${esc(r.e.aiBand)}</td>
    </tr>`).join('');
}

function doExport(){
  const {rows} = computeTally();
  const lines = ['決勝進出順位,部門,1位票,2位票,3位票,4位票,合計点,1位保護,AI予備審査点,AI予備審査ランク'];
  rows.forEach(r=> lines.push([r.finalRank, r.e.dept, r.c1, r.c2, r.c3, r.c4, r.total, r.protected_?'◎':'', r.e.aiTotal, r.e.aiBand].join(',')));
  const blob = new Blob(['﻿' + lines.join('\n')], {type:'text/csv'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = '役員予備審査_集計結果.csv';
  document.body.appendChild(a); a.click(); a.remove();
}

document.getElementById('exportBtn').onclick = doExport;
renderAll();
"""


def render_tally_html():
    entries = entries_payload()
    body = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<title>AIFES 2026 グランドフィナーレ 役員予備審査 集計</title>
<style>{TALLY_CSS}</style></head>
<body>
<header class="top">
  <div>
    <h1>AIFES 2026 グランドフィナーレ・役員予備審査 集計ツール</h1>
    <div class="who">集計係専用。役員4名から届いた「結果.json」を下に読み込んでください。</div>
  </div>
  <div class="stats"><span>読み込み済み <b id="nSubmitted">0</b>/4</span></div>
  <button id="exportBtn">集計結果をCSVで書き出す</button>
</header>
<div class="wrap" style="display:block;max-width:1100px">
  <div class="detail" style="width:100%">
    <div id="note" class="gapwarn">4名分そろうまでは暫定表示です（順位は確定しません）。</div>
    <h3 style="margin-top:0">① 役員4名分のファイルを読み込む</h3>
    <div class="upload-grid" id="slots"></div>

    <h3>② 集計結果</h3>
    <p style="font-size:12.5px;color:#707890">
      合計点＝1位×10 + 2位×8 + 3位×7 + 4位×6。緑色の行は決勝進出（上位4部門）。
      「1位保護」は、誰か1人でも1位に選んだ部門を無条件で決勝進出させるルール（合意事項）。
    </p>
    <table class="tally">
      <thead><tr><th>順位</th><th>部門</th><th>1位</th><th>2位</th><th>3位</th><th>4位</th><th>合計点</th><th>1位保護</th><th>AI予備審査（参考）</th></tr></thead>
      <tbody id="tallyBody"></tbody>
    </table>
  </div>
</div>
<script>
{TALLY_JS.replace('__OFFICERS__', js_embed(OFFICERS)).replace('__ENTRIES__', js_embed(entries))}
</script>
</body></html>"""
    return body


def main():
    for o in OFFICERS:
        fname = f"役員予備審査_{o['name']}.html"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(render_officer_html(o))
        print("wrote", fname)

    with open("役員予備審査_集計ツール.html", "w", encoding="utf-8") as f:
        f.write(render_tally_html())
    print("wrote 役員予備審査_集計ツール.html")


if __name__ == "__main__":
    main()
