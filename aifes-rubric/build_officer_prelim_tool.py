# -*- coding: utf-8 -*-
"""
役員予備審査ツール（HTML・独立版）を生成する。

- 役員4名に1人1ファイルずつ個別配布する採点ページ（役員予備審査_氏名.html）
- 集計係が4名分の結果ファイルを読み込んで1〜4位を集計するページ（役員予備審査_集計ツール.html）

Excel「04_役員予備審査投票」シートとは完全に独立（2026-08-27 ユーザー合意）。
配色は以前使っていた「AIFES2026_役員審査_伊藤英啓_コラボアクト」のネイビー×ゴールドに合わせている。
データは officer_prelim_data.py（OFFICERS / GF_ENTRIES）が唯一の定義元。
役員は点数をつけない。AI予備審査（rubric_data.py）の結果を参考値として見た上で、
1〜4位を選び、理由を書くだけ。Copilot連携・審査員別ペルソナ文書は用意しない。
一覧で1件ずつ切り替えるのではなく、全エントリーの評価パネルを縦に並べて一気に見られる構成にしている。
"""
import html
import json

from rubric_data import CRITERIA
from officer_prelim_data import OFFICERS, GF_ENTRIES, ai_total, ai_band

# 参照ツール（伊藤英啓さん・コラボアクト版）のCSS変数をそのまま踏襲した6観点用の色。
CID_COLOR = {
    "C1": "#C13A22",
    "C2": "#07756B",
    "C3": "#6244C9",
    "C4": "#A15900",
    "C5": "#B93077",
    "C6": "#155FAF",
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
            crits.append(dict(
                id=c["id"], name=c["name"], weight=c["weight"], level=lv,
                levelText=level_text, color=CID_COLOR[c["id"]],
            ))
        total = ai_total(e)
        out.append(dict(
            code=e["code"], dept=e["dept"], title=e["title"], submitter=e["submitter"],
            primary=e["primary"], attachment=e["attachment"], gaps=e["gaps"],
            aiNote=e["ai_note"], criteria=crits, aiTotal=total, aiBand=ai_band(total),
            demo=e.get("demo", False),
        ))
    return out


# ---------------------------------------------------------------------------
# CSS：以前使っていたツール（AIFES2026_役員審査_伊藤英啓_コラボアクト）の
# ネイビー×ゴールド配色・部品をそのまま踏襲。
# ---------------------------------------------------------------------------
CSS = """
:root{
  --navy:#143058; --navy-deep:#0d2140; --navy-soft:#2a4a76;
  --gold:#FFCD00; --gold-dim:#c9a300;
  --paper:#f4f6f9; --card:#ffffff; --ink:#1a2233; --mute:#6b7789; --line:#dde3ec;
  --ok:#1f9d6b; --warn:#c8102e; --amber:#b26a00;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Yu Gothic UI","Meiryo","Segoe UI",-apple-system,sans-serif;background:var(--paper);color:var(--ink);font-size:14px;line-height:1.7}
header{background:var(--navy);color:#fff;padding:14px 22px;display:flex;align-items:center;gap:20px;position:sticky;top:0;z-index:50;border-bottom:3px solid var(--gold)}
.brand{display:flex;flex-direction:column;gap:2px;min-width:230px}
.brand .en{font-size:10px;letter-spacing:.16em;color:var(--gold);font-weight:700}
.brand .jp{font-size:17px;font-weight:700;letter-spacing:.04em}
.hstat{display:flex;gap:22px;align-items:center;flex:1}
.hstat .item{display:flex;flex-direction:column;line-height:1.3}
.hstat .k{font-size:10px;color:#9fb3cd;letter-spacing:.08em}
.hstat .v{font-size:18px;font-weight:700}
.hstat .v small{font-size:11px;font-weight:400;color:#9fb3cd}
.hbar{width:180px;height:7px;background:rgba(255,255,255,.18);border-radius:4px;overflow:hidden;margin-top:6px}
.hbar>i{display:block;height:100%;background:var(--gold);width:0;transition:width .3s}
.judge{display:flex;flex-direction:column;gap:3px}
.judge label{font-size:10px;color:#9fb3cd;letter-spacing:.08em}
.judge input{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.3);color:#fff;padding:5px 9px;border-radius:4px;font:inherit;font-size:13px;width:170px;cursor:default;font-weight:700;letter-spacing:.02em}
.toolbar{background:var(--navy-deep);padding:8px 22px;display:flex;gap:8px;align-items:center;position:sticky;top:var(--header-h,64px);z-index:49;flex-wrap:wrap}
button{font:inherit;cursor:pointer;border-radius:4px;border:1px solid transparent;padding:6px 13px;transition:.15s}
.btn{background:rgba(255,255,255,.09);color:#e7edf5;border-color:rgba(255,255,255,.22)}
.btn:hover{background:rgba(255,255,255,.18)}
.btn-gold{background:var(--gold);color:var(--navy-deep);font-weight:700;border-color:var(--gold)}
.btn-gold:hover{background:#ffd93a}
.savestate{margin-left:auto;font-size:11px;color:#9fb3cd;display:flex;align-items:center;gap:6px}
.dot{width:7px;height:7px;border-radius:50%;background:var(--ok);display:inline-block}
.dot.off{background:#6b7789}
.wrap{display:grid;grid-template-columns:300px 1fr;min-height:calc(100vh - var(--stickytop,110px))}
.list{background:#fff;border-right:1px solid var(--line);overflow-y:auto;max-height:calc(100vh - var(--stickytop,110px));position:sticky;top:var(--stickytop,110px)}
.row{padding:11px 13px;border-bottom:1px solid #eef1f6;cursor:pointer;display:flex;gap:9px;align-items:flex-start;background:none;border-left:0;border-right:0;border-top:0;width:100%;text-align:left}
.row:hover{background:#f7f9fc}
.row.sel{background:#eef3fa;box-shadow:inset 3px 0 0 var(--gold)}
.row .st{width:8px;height:8px;border-radius:50%;background:#d3d9e2;margin-top:7px;flex-shrink:0}
.row.done .st{background:var(--ok)}
.row .t{font-size:12.5px;font-weight:600;line-height:1.45;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.row .m{font-size:10.5px;color:var(--mute);margin-top:3px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.row .sc{margin-left:auto;font-size:12px;font-weight:700;color:var(--navy);flex-shrink:0}
.rank-badge{background:var(--gold);color:var(--navy-deep);font-size:10px;font-weight:700;padding:1px 5px;border-radius:3px}
.demo-badge{background:#eef1f6;color:var(--mute);font-size:9.5px;font-weight:700;padding:1px 5px;border-radius:3px;letter-spacing:.04em}
.main{padding:24px 30px;overflow-y:auto;max-height:calc(100vh - var(--stickytop,110px))}
.card{max-width:900px;margin:0 auto 34px;padding-top:8px;scroll-margin-top:120px}
.card + .card{border-top:1px dashed var(--line);padding-top:34px}
.eyebrow{font-size:10px;letter-spacing:.18em;color:var(--gold-dim);font-weight:700}
h1{font-size:22px;line-height:1.45;margin:4px 0 12px;font-weight:700;color:var(--navy-deep)}
.meta{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:var(--mute);padding-bottom:14px;border-bottom:1px solid var(--line);margin-bottom:18px}
.meta b{color:var(--ink);font-weight:600}
.demoflag{margin-bottom:14px;padding:9px 13px;background:#eef1f6;border:1px dashed #c7cede;border-radius:6px;font-size:11.5px;color:var(--mute)}
.gapwarn{margin-bottom:14px;padding:9px 13px;background:#fdf0f2;border:1px solid #f0c2c9;border-radius:6px;font-size:11.5px;color:#8a2b32}
.gapwarn b{color:var(--warn);margin-right:6px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:18px 20px;margin-bottom:16px}
.panel>h2{font-size:11px;letter-spacing:.14em;color:var(--navy);font-weight:700;padding-bottom:9px;border-bottom:2px solid var(--gold);margin-bottom:15px;display:flex;align-items:center;gap:8px}
.panel>h2 span{margin-left:auto;font-size:11px;letter-spacing:0;color:var(--mute);font-weight:400}
.ainote{background:#f6f8fb;border:1px dashed #c9d4e2;border-radius:5px;padding:11px;font-size:12.5px;color:var(--mute);margin-bottom:14px}
.crit{display:grid;grid-template-columns:1fr 64px 1fr;gap:10px 16px;align-items:center;margin-bottom:12px}
.crit .cl{font-size:13px;font-weight:600}
.crit .cl small{display:block;font-weight:400;color:var(--mute);font-size:11px;margin-top:2px}
.crit .cv{font-size:20px;font-weight:800;text-align:center}
.crit .cv small{display:block;font-weight:400;color:var(--mute);font-size:10px}
.crit .cd{font-size:11.5px;color:var(--mute);line-height:1.5}
.crit .bar{height:5px;border-radius:3px;background:#eef0f6;overflow:hidden;margin-top:5px}
.crit .bar>i{display:block;height:100%}
.total{display:flex;align-items:center;gap:14px;padding:13px 16px;background:var(--navy);color:#fff;border-radius:6px;margin-top:6px}
.total .lab{font-size:11px;letter-spacing:.1em;color:#9fb3cd}
.total .num{font-size:30px;font-weight:700;line-height:1}
.total .num small{font-size:13px;color:#9fb3cd;font-weight:400}
.total .brk{margin-left:auto}
.band{font-size:12px;font-weight:800;border-radius:99px;padding:4px 12px;background:var(--gold);color:var(--navy-deep)}
.plain-links{font-size:13px}
.plain-links dt{font-weight:700;color:var(--mute);font-size:11px;margin-top:8px}
.plain-links dd{margin:2px 0 0}
.resource-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.resource-card{border:1px solid var(--line);border-radius:8px;padding:12px 14px;background:#fbfcfe}
.resource-card.empty{color:var(--mute);font-size:12.5px}
.resource-head{display:flex;gap:10px;align-items:flex-start}
.resource-icon{flex-shrink:0;width:26px;height:26px;border-radius:6px;background:var(--navy);color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700}
.resource-icon.note{background:var(--gold-dim);color:var(--navy-deep)}
.resource-title{font-size:12.5px;font-weight:700;color:var(--ink)}
.resource-url{font-size:10.5px;color:var(--mute);word-break:break-all;margin-top:2px;max-height:2.6em;overflow:hidden}
.resource-actions{display:flex;gap:8px;margin-top:10px}
.resource-actions a{flex:1;text-align:center;background:var(--navy);color:#fff;text-decoration:none;font-size:12px;font-weight:600;padding:7px 10px;border-radius:5px}
.resource-actions a:hover{background:var(--navy-soft)}
.resource-actions button{background:#fff;color:var(--navy);border:1px solid var(--navy);font-size:12px;padding:7px 10px}
.resource-actions button:hover{background:#eef3fa}
.resource-actions button.copied{background:var(--ok);color:#fff;border-color:var(--ok)}
@media (max-width:640px){.resource-grid{grid-template-columns:1fr}}
textarea{width:100%;padding:11px;font:inherit;border:1px solid var(--line);border-radius:5px;resize:vertical;line-height:1.7}
textarea:focus{outline:2px solid var(--gold);border-color:var(--gold)}
.fl label{display:block;font-size:12px;font-weight:600;margin-bottom:5px}
.fl .hint{font-size:11px;color:var(--mute);font-weight:400}
.rank-btns{display:flex;gap:8px;flex-wrap:wrap}
.rank-btn{flex:1;min-width:120px;padding:14px 8px;font-size:14px;font-weight:700;border:2px solid var(--line);background:#fff;color:var(--mute)}
.rank-btn:hover{border-color:var(--gold);color:var(--navy)}
.rank-btn.on{background:var(--gold);border-color:var(--gold);color:var(--navy-deep)}
.rank-hint{margin-top:10px;font-size:11.5px;color:var(--mute);line-height:1.6}
.rank-hint b{color:var(--gold-dim)}
.progress{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:11px 14px;background:#fff;border:1px solid var(--line);border-radius:8px;margin-bottom:18px}
.pstep{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--mute);font-weight:600}
.pstep.ok{color:var(--ok)}
.pdot{width:20px;height:20px;border-radius:50%;background:#e8ecf2;color:var(--mute);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700}
.pstep.ok .pdot{background:var(--ok);color:#fff}
.modal{position:fixed;inset:0;background:rgba(13,33,64,.55);display:none;align-items:flex-start;justify-content:center;z-index:100;padding:60px 20px;overflow-y:auto}
.modal.on{display:flex}
.mbox{background:#fff;border-radius:10px;max-width:640px;width:100%;padding:0;box-shadow:0 20px 60px rgba(13,33,64,.35)}
.mbox .mhead{background:var(--navy);color:#fff;padding:18px 26px;border-radius:10px 10px 0 0;border-bottom:3px solid var(--gold);display:flex;align-items:center;gap:14px}
.mbox .mhead h3{font-size:16px;font-weight:700}
.mbox .mhead .sub{font-size:11px;color:#9fb3cd;margin-top:2px}
.mbox .mhead button{margin-left:auto;background:rgba(255,255,255,.12);color:#fff;border:1px solid rgba(255,255,255,.35);font-size:12px;padding:6px 12px}
.mbox .mhead button:hover{background:rgba(255,255,255,.22)}
.mbody{padding:20px 26px 26px}
.result-row{display:flex;gap:14px;align-items:flex-start;padding:14px 16px;border:1px solid var(--line);border-radius:8px;margin-bottom:10px;cursor:pointer}
.result-row:hover{border-color:var(--gold);background:#fffdf2}
.result-row .rnum{flex-shrink:0;width:40px;height:40px;border-radius:50%;background:var(--gold);color:var(--navy-deep);font-weight:800;font-size:15px;display:flex;align-items:center;justify-content:center}
.result-row .rbody{flex:1;min-width:0}
.result-row .rdept{font-weight:700;font-size:13.5px}
.result-row .rtitle{font-size:11.5px;color:var(--mute);margin-top:2px}
.result-row .rreason{font-size:12px;color:#3a4356;margin-top:6px;line-height:1.6;white-space:pre-wrap}
.result-row .rsc{flex-shrink:0;font-size:11.5px;color:var(--mute);text-align:right}
.result-empty{padding:16px;text-align:center;color:var(--mute);font-size:12.5px;border:1.5px dashed var(--line);border-radius:8px}
.mbody .unranked{margin-top:18px;padding-top:14px;border-top:1px dashed var(--line);font-size:11.5px;color:var(--mute)}
"""

JS_TEMPLATE = r"""
const OFFICER = __OFFICER__;
const ENTRIES = __ENTRIES__;
const STORE_KEY = 'aifes2026_officer_prelim_' + OFFICER.key;

let state = {};
let canPersist = false;

function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function rec(code){ if(!state[code]) state[code] = {rank:'', reason:''}; return state[code]; }
function sorted_(){ return ENTRIES.slice().sort((x,y)=> y.aiTotal - x.aiTotal); }

// ---------- 提出物リンク ----------
function isUrl(s){ return typeof s === 'string' && /^https?:\/\//i.test(s.trim()); }
function shortResourceName(url){
  try{
    const clean = url.split('#')[0].split('?')[0];
    const last = clean.substring(clean.lastIndexOf('/') + 1) || clean;
    return decodeURIComponent(last).replace(/[_-]/g, ' ');
  }catch(_){ return url; }
}
function resourceCard(label, val, kind){
  if(!isUrl(val)){
    return `<div class="resource-card empty"><b>${esc(label)}</b><br>${val ? esc(val) : 'リンクが登録されていません'}</div>`;
  }
  const name = shortResourceName(val);
  return `<div class="resource-card">
    <div class="resource-head">
      <span class="resource-icon ${kind==='note'?'note':''}">${kind==='note'?'資':'作'}</span>
      <div style="min-width:0">
        <div class="resource-title">${esc(label)}：${esc(name || val)}</div>
        <div class="resource-url">${esc(val)}</div>
      </div>
    </div>
    <div class="resource-actions">
      <a href="${esc(val)}" target="_blank" rel="noopener">開く ↗</a>
      <button type="button" data-copy-text="${esc(val)}">URLをコピー</button>
    </div>
  </div>`;
}
function bindResourceCopy(){
  document.querySelectorAll('[data-copy-text]').forEach(btn=>{
    btn.onclick = async ()=>{
      try{ await navigator.clipboard.writeText(btn.dataset.copyText); }
      catch(_){}
      btn.textContent = 'コピーしました'; btn.classList.add('copied');
      setTimeout(()=>{ btn.textContent = 'URLをコピー'; btn.classList.remove('copied'); }, 1500);
    };
  });
}

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
  if(canPersist){ dot.className='dot'; txt.textContent='自動保存 有効（このPC・このブラウザのみ）。作業が終わったら必ず「結果をエクスポート」でファイルを書き出してください。'; }
  else{ dot.className='dot off'; txt.textContent='自動保存 無効。こまめに「結果をエクスポート」でファイルを書き出してください。'; }
}

// 同じ順位を別の部門につけたら、元の部門からは自動的に外す（重複防止）
function setRank(code, rank){
  const r = rec(code);
  if(String(r.rank) === String(rank)){ r.rank = ''; touch(); return; }
  ENTRIES.forEach(e=>{ if(e.code!==code && String(rec(e.code).rank)===String(rank)) rec(e.code).rank=''; });
  r.rank = String(rank);
  touch();
}
function touch(){ saveLocal(); renderAll(); }

function renderList(){
  const box = document.getElementById('rows');
  box.innerHTML = sorted_().map(e=>{
    const r = rec(e.code);
    return `<button class="row ${r.rank?'done':''}" data-code="${e.code}">
      <span class="st"></span>
      <div style="flex:1;min-width:0">
        <div class="t">${esc(e.dept)}${e.demo?' <span class=\"demo-badge\">デモ</span>':''}</div>
        <div class="m">
          <span>AI ${e.aiTotal}点・${esc(e.aiBand)}</span>
          ${r.rank ? `<span class="rank-badge">${r.rank}位</span>` : ''}
        </div>
      </div>
    </button>`;
  }).join('');
  box.querySelectorAll('.row').forEach(el=> el.onclick = ()=>{
    document.getElementById('card-' + el.dataset.code).scrollIntoView({behavior:'smooth', block:'start'});
  });

  const done = ENTRIES.filter(e=>rec(e.code).rank).length;
  document.getElementById('hDoneNum').textContent = done;
  document.getElementById('hDoneTotal').textContent = ENTRIES.length;
  document.getElementById('hBar').style.width = (ENTRIES.length ? done/ENTRIES.length*100 : 0) + '%';

  const realRanked = ENTRIES.filter(e=>!e.demo && rec(e.code).rank).length;
  document.getElementById('resultsBtnCount').textContent = realRanked;
}

function critRow(c){
  return `<div class="crit">
    <div class="cl">${esc(c.name)}<small>配点 ${c.weight}点</small></div>
    <div class="cv" style="color:${c.color}">${c.level || '—'}<small>/5</small>
      <div class="bar"><i style="width:${c.level? c.level/5*100:0}%;background:${c.color}"></i></div>
    </div>
    <div class="cd">${esc(c.levelText)}</div>
  </div>`;
}

function cardHtml(e){
  const r = rec(e.code);
  return `<div class="card" id="card-${e.code}">
    <div class="eyebrow">${esc(e.code)}</div>
    <h1>${esc(e.dept)}</h1>
    <div class="meta"><span><b>${esc(e.title)}</b></span><span>提出者：${esc(e.submitter)}</span></div>

    <div class="progress">
      ${[['1〜4位を選ぶ', !!r.rank],['理由を書く', !!r.reason.trim()]].map(([lab,ok])=>
        `<span class="pstep ${ok?'ok':''}"><span class="pdot">${ok?'✓':'-'}</span>${lab}</span>`).join('')}
    </div>

    ${e.demo ? `<div class="demoflag">これは動作確認用のダミーエントリーです。実際の応募内容ではありません。</div>` : ''}
    ${e.gaps.length ? `<div class="gapwarn"><b>提出物の不足</b>${e.gaps.map(esc).join(' / ')}</div>` : ''}

    <div class="panel">
      <h2>AI予備審査（参考値）<span>編集不可</span></h2>
      ${e.aiNote ? `<div class="ainote">${esc(e.aiNote)}</div>` : ''}
      ${e.criteria.map(critRow).join('')}
      <div class="total">
        <div>
          <div class="lab">最終スコア</div>
          <div class="num">${e.aiTotal}<small> / 100</small></div>
        </div>
        <div class="brk"><span class="band">${esc(e.aiBand)}ランク</span></div>
      </div>
    </div>

    <div class="panel">
      <h2>提出物<span>GFに手順書の提出はありません</span></h2>
      <div class="resource-grid">
        ${resourceCard('作品', e.primary, 'work')}
        ${e.attachment ? resourceCard('補足資料', e.attachment, 'note') : ''}
      </div>
    </div>

    <div class="panel">
      <h2>STEP 1：1〜4位を選ぶ</h2>
      <div class="rank-btns">
        ${[1,2,3,4].map(n=>`<button class="rank-btn ${String(r.rank)===String(n)?'on':''}" data-code="${e.code}" data-rank="${n}">${n}位に選ぶ</button>`).join('')}
      </div>
      <div class="rank-hint">${r.rank ? `<b>${r.rank}位</b>に選んでいます。もう一度押すと解除できます。同じ順位を他の部門につけると、こちらの順位は自動で外れます。` : '決勝に進めたい順に、1位から選んでください。選ばない部門はそのままで構いません。'}</div>
    </div>

    <div class="panel">
      <h2>STEP 2：理由を書く<span>任意・集計係が参照します</span></h2>
      <div class="fl">
        <textarea data-code="${e.code}" rows="3" placeholder="例）AIの点数以上に、部門全体を巻き込んだ広がり方に説得力がある。">${esc(r.reason)}</textarea>
      </div>
    </div>
  </div>`;
}

function renderMain(){
  document.getElementById('main').innerHTML = sorted_().map(cardHtml).join('');
  document.querySelectorAll('[data-rank]').forEach(b=> b.onclick = ()=> setRank(b.dataset.code, b.dataset.rank));
  document.querySelectorAll('textarea[data-code]').forEach(ta=>{
    ta.oninput = ()=>{ rec(ta.dataset.code).reason = ta.value; saveLocal(); };
  });
  bindResourceCopy();
}

function renderAll(){ renderList(); renderMain(); }

function renderResultsModal(){
  const ranked = ENTRIES.filter(e=>!e.demo && rec(e.code).rank)
    .sort((a,b)=> (+rec(a.code).rank) - (+rec(b.code).rank));
  const unranked = ENTRIES.filter(e=>!e.demo && !rec(e.code).rank);
  const demoRanked = ENTRIES.filter(e=>e.demo && rec(e.code).rank);

  const rows = ranked.map(e=>{
    const r = rec(e.code);
    return `<div class="result-row" data-code="${e.code}">
      <div class="rnum">${r.rank}位</div>
      <div class="rbody">
        <div class="rdept">${esc(e.dept)}</div>
        <div class="rtitle">${esc(e.title)}</div>
        ${r.reason.trim() ? `<div class="rreason">${esc(r.reason)}</div>` : `<div class="rreason" style="color:#aab0bd">理由は未入力です</div>`}
      </div>
      <div class="rsc">AI ${e.aiTotal}点<br>${esc(e.aiBand)}ランク</div>
    </div>`;
  }).join('');

  const body =
    (ranked.length ? rows : `<div class="result-empty">まだ順位をつけた部門がありません。一覧から1〜4位を選んでください。</div>`) +
    (unranked.length ? `<div class="unranked">順位をつけていない部門（${unranked.length}件）：${unranked.map(e=>esc(e.dept)).join(' / ')}</div>` : '') +
    (demoRanked.length ? `<div class="unranked">※デモ部門（${demoRanked.map(e=>esc(e.dept)).join(' / ')}）につけた順位は、動作確認用のため最終結果・エクスポートには含まれません。</div>` : '');

  document.getElementById('resultsBody').innerHTML = body;
  document.querySelectorAll('.result-row').forEach(row=>{
    row.onclick = ()=>{
      closeResults();
      document.getElementById('card-' + row.dataset.code).scrollIntoView({behavior:'smooth', block:'start'});
    };
  });
}
function openResults(){ renderResultsModal(); document.getElementById('resultsModal').classList.add('on'); }
function closeResults(){ document.getElementById('resultsModal').classList.remove('on'); }

function doExport(){
  const payload = {
    officer: OFFICER, exportedAt: new Date().toISOString(),
    ranks: ENTRIES.filter(e=>!e.demo).map(e=>({code:e.code, dept:e.dept, rank: rec(e.code).rank || null, reason: rec(e.code).reason || ''})),
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

function fitSticky(){
  const h = document.querySelector('header').offsetHeight;
  const t = document.querySelector('.toolbar').offsetHeight;
  document.documentElement.style.setProperty('--header-h', h + 'px');
  document.documentElement.style.setProperty('--stickytop', (h + t) + 'px');
}

loadLocal();
document.getElementById('exportBtn').onclick = doExport;
document.getElementById('importInput').onchange = (ev)=>{ if(ev.target.files[0]) doImport(ev.target.files[0]); };
document.getElementById('resultsBtn').onclick = openResults;
document.getElementById('resultsClose').onclick = closeResults;
document.getElementById('resultsModal').onclick = (ev)=>{ if(ev.target.id==='resultsModal') closeResults(); };
document.addEventListener('keydown', (ev)=>{ if(ev.key==='Escape') closeResults(); });
paintSave();
renderAll();
fitSticky();
window.addEventListener('resize', fitSticky);
"""


def render_officer_html(officer):
    entries = entries_payload()
    real_n = sum(1 for e in entries if not e["demo"])
    demo_n = len(entries) - real_n
    demo_note = f"（うちデモ {demo_n} 件を含む）" if demo_n else ""
    body = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AIFES 2026 グランドフィナーレ 役員予備審査 — {E(officer['name'])}</title>
<style>{CSS}</style></head>
<body>
<header>
  <div class="brand">
    <div class="en">AIFES 2026 GRAND FINALE</div>
    <div class="jp">役員予備審査</div>
  </div>
  <div class="hstat">
    <div class="item">
      <span class="k">進捗</span>
      <span class="v"><span id="hDoneNum">0</span><small> / <span id="hDoneTotal">{len(entries)}</span> 件{demo_note}</small></span>
      <div class="hbar"><i id="hBar"></i></div>
    </div>
  </div>
  <div class="judge">
    <label>担当役員</label>
    <input readonly value="{E(officer['name'])}">
  </div>
</header>
<div class="toolbar">
  <button class="btn-gold" id="resultsBtn">✓ 自分の最終結果を見る（<span id="resultsBtnCount">0</span>/4）</button>
  <label class="btn">結果を読み込む<input id="importInput" type="file" accept="application/json" style="display:none"></label>
  <button class="btn" id="exportBtn">結果をエクスポート</button>
  <div class="savestate"><span class="dot" id="saveDot"></span><span id="saveTxt"></span></div>
</div>
<div class="wrap">
  <div class="list" id="rows"></div>
  <div class="main" id="main"></div>
</div>
<div class="modal" id="resultsModal">
  <div class="mbox">
    <div class="mhead">
      <div>
        <h3>あなたの最終結果</h3>
        <div class="sub">{E(officer['name'])} さんが選んだ1〜4位</div>
      </div>
      <button id="resultsClose">閉じる ✕</button>
    </div>
    <div class="mbody" id="resultsBody"></div>
  </div>
</div>
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
tr.advance{background:#eafaf1}
.upload-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:16px 0}
.upload-grid .slot{border:1.5px dashed var(--line);border-radius:10px;padding:16px;text-align:center;font-size:12.5px}
.upload-grid .slot.done{border-color:var(--ok);background:#eafaf1}
.upload-grid .slot input{display:block;margin:10px auto 0}
"""

TALLY_JS = r"""
const OFFICERS = __OFFICERS__;
const ENTRIES = __ENTRIES__.filter(e=>!e.demo);
let ballots = {};

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
          const map = {};
          (data.ranks||[]).forEach(x=>{ if(x.rank) map[x.code]=String(x.rank); });
          ballots[inp.dataset.key] = map;
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
  rows.sort((a,b)=> b.key - a.key);
  rows.forEach((r,i)=> r.finalRank = i+1);
  return rows;
}

function renderAll(){
  renderSlots();
  const rows = computeTally();
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
  const rows = computeTally();
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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AIFES 2026 グランドフィナーレ 役員予備審査 集計ツール</title>
<style>{TALLY_CSS}</style></head>
<body>
<header>
  <div class="brand">
    <div class="en">AIFES 2026 GRAND FINALE</div>
    <div class="jp">役員予備審査・集計ツール</div>
  </div>
  <div class="hstat">
    <div class="item"><span class="k">読み込み済み</span><span class="v"><span id="nSubmitted">0</span><small> / 4 名</small></span></div>
  </div>
</header>
<div class="toolbar">
  <button class="btn-gold" id="exportBtn">集計結果をCSVで書き出す</button>
</div>
<div class="main" style="max-width:1100px;margin:0 auto;max-height:none;overflow:visible">
  <div class="card" style="max-width:none">
    <div id="note" class="gapwarn" style="background:#fffbea;border-color:#f0dfa0;color:#7a5b00"><b>準備中</b>4名分そろうまでは暫定表示です（順位は確定しません）。</div>
    <div class="panel">
      <h2>① 役員4名分のファイルを読み込む</h2>
      <div class="upload-grid" id="slots"></div>
    </div>
    <div class="panel">
      <h2>② 集計結果</h2>
      <p style="font-size:12.5px;color:var(--mute);margin-bottom:10px">
        合計点＝1位×10 + 2位×8 + 3位×7 + 4位×6。緑色の行は決勝進出（上位4部門）。
        「1位保護」は、誰か1人でも1位に選んだ部門を無条件で決勝進出させるルール（合意事項）。
      </p>
      <table class="tally">
        <thead><tr><th>順位</th><th>部門</th><th>1位</th><th>2位</th><th>3位</th><th>4位</th><th>合計点</th><th>1位保護</th><th>AI予備審査（参考）</th></tr></thead>
        <tbody id="tallyBody"></tbody>
      </table>
    </div>
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
