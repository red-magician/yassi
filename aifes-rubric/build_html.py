# -*- coding: utf-8 -*-
"""rubric_data.py から審査員向け説明資料（HTML）を生成する。"""
import html
from rubric_data import CRITERIA, JUDGES, FLAGS, BANDS, TIEBREAK, META, WEIGHTS

J = {j["no"]: j for j in JUDGES}
E = html.escape
MAXW = max(c["weight"] for c in CRITERIA)


def axes_for(no):
    out = []
    for c in CRITERIA:
        ms = [(m, n) for jn, m, n in c["sources"] if jn == no]
        if ms:
            out.append((c, "◎" if any(m == "◎" for m, _ in ms) else "○", [n for _, n in ms]))
    return out


# ---------------------------------------------------------------- 観点カード
cards = []
for c in CRITERIA:
    lv = "".join(
        f'<li><span class="lvn">{n}</span><span class="lvt">{E(t)}</span></li>'
        for n, t in zip([5, 4, 3, 2, 1], c["levels"]))
    src = "".join(
        f'<li class="{"m-d" if m == "◎" else "m-o"}"><span class="mk">{m}</span>'
        f'<span class="jn">{E(J[jn]["name"])}</span>'
        f'<span class="jq">{E(n)}</span></li>'
        for jn, m, n in c["sources"])
    n_d = sum(1 for _, m, _ in c["sources"] if m == "◎")
    n_o = sum(1 for _, m, _ in c["sources"] if m == "○")
    cards.append(f"""
<article class="crit" id="{c['id']}">
  <header class="crit-h">
    <div class="crit-id">{c['id']}</div>
    <div class="crit-t">
      <h3>{E(c['name'])}</h3>
      <p class="q">{E(c['question'])}</p>
    </div>
    <div class="crit-w"><span class="wn">{c['weight']}</span><span class="wu">点</span></div>
  </header>
  <div class="wbar"><i style="width:{c['weight'] / MAXW * 100:.1f}%"></i></div>
  <p class="crit-def">{E(c['definition'])}</p>
  <div class="crit-body">
    <div class="lv-wrap">
      <h4>レベルの目安</h4>
      <ol class="lv">{lv}</ol>
    </div>
    <div class="src-wrap">
      <h4>この観点の出所 <span class="cnt">◎{n_d} ／ ○{n_o}</span></h4>
      <ul class="src">{src}</ul>
    </div>
  </div>
</article>""")

# ---------------------------------------------------------------- 対応表
mhead = "".join(
    f'<th><a href="#{c["id"]}"><span class="mid">{c["id"]}</span>'
    f'<span class="msh">{E(c["short"])}</span><span class="mwt">{c["weight"]}点</span></a></th>'
    for c in CRITERIA)
mrows = []
for j in JUDGES:
    tds = []
    for c in CRITERIA:
        ms = [m for jn, m, _ in c["sources"] if jn == j["no"]]
        if not ms:
            tds.append('<td class="e"></td>')
        elif "◎" in ms:
            tds.append('<td class="d"><span>◎</span></td>')
        else:
            tds.append('<td class="o"><span>○</span></td>')
    mrows.append(
        f'<tr><th scope="row"><a href="#j{j["no"]}"><b>{E(j["name"])}</b>'
        f'<i>{E(j["title"])}</i></a></th>{"".join(tds)}</tr>')
mfoot = "".join(f'<td class="tw">{c["weight"]}</td>' for c in CRITERIA)

# ---------------------------------------------------------------- 審査員カード
jcards = []
for j in JUDGES:
    ax = axes_for(j["no"])
    chips = "".join(
        f'<a class="chip {"c-d" if m == "◎" else "c-o"}" href="#{c["id"]}">'
        f'<span class="mk">{m}</span>{c["id"]} {E(c["short"])}</a>'
        for c, m, _ in ax)
    jcards.append(f"""
<article class="jc" id="j{j['no']}">
  <div class="jc-h"><h3>{E(j['name'])}</h3><p>{E(j['title'])}</p></div>
  <blockquote>{E(j['gf'])}</blockquote>
  <div class="chips">{chips}</div>
</article>""")

# ---------------------------------------------------------------- 配点の導出
deriv = "".join(
    f'<tr><th scope="row">{c["id"]} {E(c["short"])}</th>'
    f'<td>{sum(1 for _, m, _ in c["sources"] if m == "◎")}</td>'
    f'<td>{sum(1 for _, m, _ in c["sources"] if m == "○")}</td>'
    f'<td class="num">{c["raw"]:.1f}</td>'
    f'<td class="num">{c["exact"]:.1f}%</td>'
    f'<td class="num strong">{c["weight"]}</td></tr>'
    for c in CRITERIA)
raw_total = sum(c["raw"] for c in CRITERIA)

flags = "".join(f"""
<article class="flag">
  <div class="fid">{f['id']}</div>
  <div class="fbody">
    <h3>{E(f['name'])}</h3>
    <p class="fd"><b>見分け方</b>{E(f['detect'])}</p>
    <p class="fc"><b>かかる上限</b>{
      "／".join(f"{cid} {E(next(x['short'] for x in CRITERIA if x['id'] == cid))} はレベル{cap}以下"
                for cid, cap in f['cap'].items())}</p>
    <p class="fb">{E(f['basis'])}</p>
  </div>
</article>""" for f in FLAGS)

bands = "".join(
    f'<tr><td class="bl b-{lab}">{lab}</td>'
    f'<td class="num">{cut}点以上</td><td>{E(desc)}</td></tr>' if cut
    else f'<tr><td class="bl b-{lab}">{lab}</td><td class="num">50点未満</td><td>{E(desc)}</td></tr>'
    for cut, lab, desc in BANDS)

CSS = """
*{box-sizing:border-box}
:root{
  --paper:#F4F6F9; --card:#FFFFFF; --ink:#141F33; --ink2:#3C4B66; --mute:#6C7C97;
  --line:#D7DEE9; --line2:#E9EEF5;
  --navy:#1F3864; --navy2:#2E4E86; --gold:#9C7418; --gold-s:#F3EBD7;
  --ok:#2C6B4F; --warn:#9A5B12; --bad:#8E3838;
  --shadow:0 1px 2px rgba(20,31,51,.06),0 8px 24px -12px rgba(20,31,51,.18);
  --disp:"Hiragino Mincho ProN","Yu Mincho",YuMincho,"Noto Serif JP","Songti SC",serif;
  --body:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic","Noto Sans JP","Meiryo",sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --paper:#0D1421; --card:#151F31; --ink:#E7ECF4; --ink2:#B7C3D6; --mute:#8595AE;
  --line:#28344A; --line2:#1E2A3D;
  --navy:#8FB0E6; --navy2:#A9C4F0; --gold:#D8B25A; --gold-s:#2C2515;
  --ok:#6FBF95; --warn:#D9A05B; --bad:#D98080;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 28px -14px rgba(0,0,0,.7);
}}
:root[data-theme="dark"]{
  --paper:#0D1421; --card:#151F31; --ink:#E7ECF4; --ink2:#B7C3D6; --mute:#8595AE;
  --line:#28344A; --line2:#1E2A3D;
  --navy:#8FB0E6; --navy2:#A9C4F0; --gold:#D8B25A; --gold-s:#2C2515;
  --ok:#6FBF95; --warn:#D9A05B; --bad:#D98080;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 28px -14px rgba(0,0,0,.7);
}
:root[data-theme="light"]{
  --paper:#F4F6F9; --card:#FFFFFF; --ink:#141F33; --ink2:#3C4B66; --mute:#6C7C97;
  --line:#D7DEE9; --line2:#E9EEF5;
  --navy:#1F3864; --navy2:#2E4E86; --gold:#9C7418; --gold-s:#F3EBD7;
  --ok:#2C6B4F; --warn:#9A5B12; --bad:#8E3838;
  --shadow:0 1px 2px rgba(20,31,51,.06),0 8px 24px -12px rgba(20,31,51,.18);
}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);
  font-size:15px;line-height:1.85;-webkit-font-smoothing:antialiased;
  font-feature-settings:"palt" 1}
.wrap{max-width:980px;margin:0 auto;padding:0 24px 96px}
section{margin-top:72px}
h2{font-family:var(--disp);font-size:26px;line-height:1.4;margin:0 0 6px;
  letter-spacing:.02em;text-wrap:balance;font-weight:600}
.sec-h{display:flex;align-items:baseline;gap:14px;padding-bottom:12px;
  border-bottom:2px solid var(--navy);margin-bottom:28px;flex-wrap:wrap}
.sec-n{font-family:var(--mono);font-size:12px;color:var(--gold);letter-spacing:.16em;
  font-weight:700;flex:none}
.sec-s{color:var(--mute);font-size:13px;margin:0;flex:1 1 260px;line-height:1.7}
.lede{font-size:16px;color:var(--ink2);max-width:66ch;line-height:2}

/* hero */
header.hero{background:var(--navy);color:#fff;padding:0;margin-bottom:0;
  border-bottom:4px solid var(--gold)}
:root[data-theme="dark"] header.hero,
:root:not([data-theme="light"]) header.hero{background:linear-gradient(180deg,#16243E,#101A2C)}
@media (prefers-color-scheme:light){:root:not([data-theme="dark"]) header.hero{background:#1F3864}}
:root[data-theme="light"] header.hero{background:#1F3864}
.hero-in{max-width:980px;margin:0 auto;padding:52px 24px 44px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.22em;
  color:#D9BE79;margin:0 0 18px;font-weight:700}
.hero h1{font-family:var(--disp);font-size:clamp(28px,4.6vw,42px);line-height:1.35;
  margin:0 0 18px;font-weight:600;letter-spacing:.01em;text-wrap:balance;color:#fff}
.hero p{margin:0;max-width:62ch;color:#C4D2E8;font-size:15px;line-height:2}
.flow{display:flex;align-items:center;gap:14px;margin-top:32px;flex-wrap:wrap}
.flow .b{border:1px solid rgba(255,255,255,.28);border-radius:2px;padding:10px 16px;
  text-align:center;min-width:112px}
.flow .b b{display:block;font-family:var(--mono);font-size:22px;color:#E8C87C;line-height:1.3}
.flow .b span{font-size:11px;color:#AFC1DC;letter-spacing:.06em}
.flow .ar{color:#7C93B8;font-size:18px}
.flow .b.hi{border-color:var(--gold);background:rgba(216,178,90,.1)}

/* 観点カード */
.crit{background:var(--card);border:1px solid var(--line);border-radius:3px;
  margin-bottom:20px;box-shadow:var(--shadow);overflow:hidden;scroll-margin-top:20px}
.crit-h{display:flex;align-items:flex-start;gap:16px;padding:20px 24px 12px}
.crit-id{font-family:var(--mono);font-weight:700;font-size:13px;color:#fff;
  background:var(--navy);padding:4px 9px;border-radius:2px;flex:none;margin-top:4px;
  letter-spacing:.04em}
:root[data-theme="dark"] .crit-id{color:#0D1421}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .crit-id{color:#0D1421}}
.crit-t{flex:1 1 auto;min-width:0}
.crit-t h3{font-family:var(--disp);font-size:20px;margin:0;font-weight:600;line-height:1.45}
.q{margin:4px 0 0;color:var(--gold);font-size:13.5px;line-height:1.7}
.crit-w{flex:none;text-align:right;line-height:1}
.wn{font-family:var(--mono);font-size:32px;font-weight:700;color:var(--navy);
  font-variant-numeric:tabular-nums}
.wu{font-size:12px;color:var(--mute);margin-left:2px}
.wbar{height:3px;background:var(--line2);margin:0 24px}
.wbar i{display:block;height:3px;background:var(--gold)}
.crit-def{margin:14px 24px 0;color:var(--ink2);font-size:13.5px;line-height:1.9}
.crit-body{display:grid;grid-template-columns:1.35fr 1fr;gap:0;margin-top:18px;
  border-top:1px solid var(--line2)}
.crit-body>div{padding:18px 24px 22px}
.src-wrap{border-left:1px solid var(--line2);background:var(--line2)}
h4{font-size:11px;letter-spacing:.14em;color:var(--mute);margin:0 0 12px;
  font-weight:700;text-transform:uppercase;display:flex;justify-content:space-between;gap:8px}
.cnt{font-family:var(--mono);color:var(--gold);letter-spacing:.04em}
ol.lv{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}
ol.lv li{display:flex;gap:11px;align-items:flex-start}
.lvn{font-family:var(--mono);font-weight:700;font-size:11px;flex:none;width:22px;height:22px;
  display:grid;place-items:center;border-radius:50%;margin-top:3px;
  background:var(--line2);color:var(--ink2);border:1px solid var(--line)}
ol.lv li:first-child .lvn{background:var(--gold);color:#fff;border-color:var(--gold)}
:root[data-theme="dark"] ol.lv li:first-child .lvn{color:#0D1421}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) ol.lv li:first-child .lvn{color:#0D1421}}
.lvt{font-size:12.5px;line-height:1.75;color:var(--ink2)}
ol.lv li:first-child .lvt{color:var(--ink)}
ul.src{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px}
ul.src li{display:grid;grid-template-columns:16px 1fr;column-gap:8px;row-gap:1px;
  font-size:12px;line-height:1.65}
.mk{font-size:12px;line-height:1.6;font-weight:700}
.m-d .mk{color:var(--gold)}
.m-o .mk{color:var(--mute)}
.jn{font-weight:700;color:var(--ink)}
.jq{grid-column:2;color:var(--mute);font-size:11.5px;line-height:1.6}
.m-o .jn{font-weight:400;color:var(--ink2)}

/* 対応表 */
.tscroll{overflow-x:auto;border:1px solid var(--line);border-radius:3px;background:var(--card);
  box-shadow:var(--shadow)}
table.mx{border-collapse:collapse;width:100%;min-width:720px;font-size:13px}
table.mx th,table.mx td{border-bottom:1px solid var(--line2);padding:0}
table.mx thead th{background:var(--navy);padding:10px 6px;vertical-align:bottom;
  border-bottom:none;text-align:center}
table.mx thead th:first-child{text-align:left;padding-left:16px}
table.mx thead th a{text-decoration:none;display:block}
.mid{display:block;font-family:var(--mono);font-size:10px;color:#D9BE79;letter-spacing:.1em}
.msh{display:block;font-size:12px;color:#fff;font-weight:700;line-height:1.4;margin:2px 0}
.mwt{display:block;font-family:var(--mono);font-size:10px;color:#9DB3D4}
table.mx tbody th{text-align:left;padding:0}
table.mx tbody th a{display:block;padding:9px 16px;text-decoration:none;color:inherit}
table.mx tbody th a:hover{background:var(--line2)}
table.mx tbody th b{display:block;font-size:13px;font-weight:700;color:var(--ink)}
table.mx tbody th i{display:block;font-style:normal;font-size:10.5px;color:var(--mute);
  line-height:1.5}
table.mx td{text-align:center;font-size:15px;font-weight:700}
table.mx td.d{color:var(--gold);background:var(--gold-s)}
table.mx td.o{color:var(--mute)}
table.mx tbody tr:hover td{background:var(--line2)}
table.mx tbody tr:hover td.d{background:var(--gold-s)}
table.mx tfoot td,table.mx tfoot th{background:var(--line2);font-family:var(--mono);
  font-weight:700;padding:9px 6px;text-align:center;color:var(--navy);font-size:14px}
table.mx tfoot th{text-align:right;padding-right:14px;font-family:var(--body);
  font-size:11px;color:var(--mute);letter-spacing:.08em}
.legend{display:flex;gap:22px;margin-top:14px;font-size:12px;color:var(--mute);flex-wrap:wrap}
.legend b{color:var(--gold);font-size:14px;margin-right:4px}
.legend .om{color:var(--ink2);font-size:14px;margin-right:4px;font-weight:700}

/* 審査員カード */
.jgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.jc{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:18px 20px 16px;
  box-shadow:var(--shadow);scroll-margin-top:20px;display:flex;flex-direction:column;gap:12px}
.jc-h h3{font-family:var(--disp);font-size:17px;margin:0;font-weight:600}
.jc-h p{margin:1px 0 0;font-size:11px;color:var(--mute);line-height:1.5}
.jc blockquote{margin:0;padding:0 0 0 14px;border-left:2px solid var(--gold);
  font-size:12.5px;line-height:1.85;color:var(--ink2);flex:1}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{display:inline-flex;align-items:center;gap:5px;font-size:11px;text-decoration:none;
  padding:3px 9px;border-radius:2px;border:1px solid var(--line);color:var(--ink2);
  font-family:var(--mono);letter-spacing:.02em}
.chip .mk{font-size:11px}
.c-d{border-color:var(--gold);background:var(--gold-s);color:var(--ink)}
.chip:hover{border-color:var(--navy)}

/* 導出テーブル */
table.dv,table.bd{border-collapse:collapse;width:100%;background:var(--card);
  border:1px solid var(--line);font-size:13px;box-shadow:var(--shadow)}
table.dv th,table.dv td,table.bd th,table.bd td{border-bottom:1px solid var(--line2);
  padding:9px 14px;text-align:left}
table.dv thead th,table.bd thead th{background:var(--line2);font-size:11px;
  letter-spacing:.08em;color:var(--mute);font-weight:700}
table.dv tbody th{font-weight:700}
.num{font-family:var(--mono);text-align:right;font-variant-numeric:tabular-nums}
table.dv thead th.num,table.dv tfoot td.num{text-align:right}
.strong{color:var(--gold);font-weight:700;font-size:15px}
table.dv tfoot td,table.dv tfoot th{background:var(--line2);font-weight:700}
.formula{font-family:var(--mono);font-size:12.5px;background:var(--card);
  border:1px solid var(--line);border-left:3px solid var(--gold);padding:12px 16px;
  margin:0 0 18px;color:var(--ink2);overflow-x:auto;line-height:1.9}

/* フラグ */
.flag{display:grid;grid-template-columns:56px 1fr;background:var(--card);
  border:1px solid var(--line);border-radius:3px;margin-bottom:12px;box-shadow:var(--shadow)}
.fid{background:var(--navy);color:#fff;font-family:var(--mono);font-weight:700;
  display:grid;place-items:center;font-size:14px}
:root[data-theme="dark"] .fid{color:#0D1421}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .fid{color:#0D1421}}
.fbody{padding:14px 18px}
.fbody h3{margin:0 0 8px;font-size:15px;font-family:var(--disp);font-weight:600}
.fbody p{margin:0 0 6px;font-size:12.5px;line-height:1.75;color:var(--ink2)}
.fbody p b{display:inline-block;min-width:74px;font-size:10.5px;letter-spacing:.08em;
  color:var(--mute)}
.fc{color:var(--warn)!important;font-weight:700}
.fb{color:var(--mute)!important;font-size:11.5px!important;border-top:1px dashed var(--line);
  padding-top:8px;margin-top:10px!important}

/* 判定 */
.bl{font-family:var(--mono);font-weight:700;font-size:17px;width:56px;text-align:center}
.b-S{color:var(--gold)} .b-A{color:var(--ok)} .b-B{color:var(--warn)} .b-C{color:var(--mute)}
ol.tb{margin:16px 0 0;padding-left:20px;font-size:13px;color:var(--ink2);line-height:2}
ol.tb li::marker{color:var(--gold);font-family:var(--mono);font-weight:700}

.note{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--navy);
  padding:16px 20px;font-size:13px;color:var(--ink2);line-height:1.9;margin-top:24px}
.note b{color:var(--ink)}
footer{margin-top:80px;padding-top:20px;border-top:1px solid var(--line);
  font-size:11.5px;color:var(--mute);line-height:1.9}
a{color:var(--navy2)}
a:focus-visible,.chip:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
@media (max-width:760px){
  .crit-body{grid-template-columns:1fr}
  .src-wrap{border-left:none;border-top:1px solid var(--line2)}
  .crit-h{flex-wrap:wrap}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""


def sec(n, title, sub=""):
    return (f'<div class="sec-h"><span class="sec-n">{n}</span><h2>{title}</h2>'
            f'<p class="sec-s">{sub}</p></div>')


HTML = f"""<title>AIFES 2026 グランドフィナーレ AI予備審査ルーブリック</title>
<style>{CSS}</style>
<header class="hero">
  <div class="hero-in">
    <p class="eyebrow">AIFES 2026 ／ GRAND FINALE ／ 予備審査</p>
    <h1>審査員12名の言葉を、<br>6つの観点にまとめました。</h1>
    <p>グランドフィナーレの予備審査を、審査員のみなさまに12回ご負担いただくことなくAIで一次実施するための共通ルーブリックです。
       12名それぞれのコメントを6観点に集約しているため、1回の採点で全員の観点が反映されます。
       本資料は、<b style="color:#E8C87C">ご自身のコメントがどの観点のどこに入っているか</b>をご確認いただくためのものです。</p>
    <div class="flow">
      <div class="b"><b>12</b><span>審査員コメント</span></div>
      <span class="ar">→</span>
      <div class="b hi"><b>6</b><span>評価観点</span></div>
      <span class="ar">→</span>
      <div class="b"><b>100</b><span>点満点</span></div>
      <span class="ar">→</span>
      <div class="b"><b>S / A / B / C</b><span>予備審査判定</span></div>
    </div>
  </div>
</header>

<div class="wrap">

<section>
  {sec("01", "この資料の読み方", "1分で全体像、5分でご自身のコメントの反映先まで確認できます。")}
  <p class="lede">
    集約の元にしたのは、審査員コメント一覧の<b>「グランドフィナーレコメント」</b>です。これを主（◎）として観点の骨格をつくり、
    各ステージ向けの「審査コメント」を従（○）として補助的に織り込んでいます。
    配点は担当者が決め打ちしたものではなく、<b>各観点に何名の審査員が言及したかを数えて機械的に算出</b>しています。
    どの発言がどの観点の何点分になっているかは、すべて追える形で本資料に記載しています。
  </p>
</section>

<section>
  {sec("02", "6つの評価観点と配点", "レベル5が満点相当。加重得点 ＝ レベル ÷ 5 × 配点。")}
  {"".join(cards)}
</section>

<section>
  {sec("03", "審査員 × 観点 対応表",
       "◎＝グランドフィナーレコメントが直接この観点の根拠。○＝審査コメントを補助的に反映。12名全員が最低1観点に◎で入っています。")}
  <div class="tscroll">
    <table class="mx">
      <thead><tr><th>審査員</th>{mhead}</tr></thead>
      <tbody>{"".join(mrows)}</tbody>
      <tfoot><tr><th>配点</th>{mfoot}</tr></tfoot>
    </table>
  </div>
  <div class="legend">
    <span><b>◎</b>グランドフィナーレコメントが直接の根拠（重み 1.0）</span>
    <span><span class="om">○</span>審査コメントを補助的に反映（重み 0.5）</span>
    <span>審査員名・観点名はクリックで該当箇所へ移動します</span>
  </div>
</section>

<section>
  {sec("04", "あなたのコメントが入った観点",
       "グランドフィナーレコメントの原文と、そこから導かれた観点です。")}
  <div class="jgrid">{"".join(jcards)}</div>
</section>

<section>
  {sec("05", "配点の決め方", "恣意的な重み付けをしていないことを確認いただくための計算過程です。")}
  <p class="formula">言及重み ＝ ◎の数 × 1.0 ＋ ○の数 × 0.5<br>
     配点 ＝ 言及重み ÷ {raw_total:.1f}（全観点の合計）× 100　→　最も近い10点刻みに丸める（合計は100のまま）</p>
  <table class="dv">
    <thead><tr><th>観点</th><th>◎</th><th>○</th><th class="num">言及重み</th>
      <th class="num">正規化</th><th class="num">配点<br><span style="font-weight:400;font-size:9px">10点刻み</span></th></tr></thead>
    <tbody>{deriv}</tbody>
    <tfoot><tr><th>合計</th>
      <td>{sum(1 for c in CRITERIA for _, m, _ in c["sources"] if m == "◎")}</td>
      <td>{sum(1 for c in CRITERIA for _, m, _ in c["sources"] if m == "○")}</td>
      <td class="num">{raw_total:.1f}</td><td class="num">100.0%</td>
      <td class="num strong">{sum(WEIGHTS)}</td></tr></tfoot>
  </table>
  <div class="note">
    <b>この設計で意図的に外していること。</b>
    役職による重み付けは行っていません。社長・取締役のコメントも執行役員のコメントも、言及として同じ1件として数えています。
    予備審査は足切りと順位づけのための一次スクリーニングであり、最終的な意思決定は審査員のみなさまによる人手審査で行うためです。
  </div>
</section>

<section>
  {sec("06", "前提フラグ", "加点材料ではなく、該当した観点にレベルの上限をかける仕組みです。")}
  <p class="lede" style="margin-bottom:24px">
    「生産性向上は企業として取り組むべき前提」（櫻田）、「何をAIで実現したかよりも文化」（中山）といった、
    <b>それ単体では評価に値しない</b>という趣旨のコメントは、加点ではなく天井として実装しています。
    該当した応募は、その観点で一定レベル以上をつけられません。
  </p>
  {flags}
</section>

<section>
  {sec("07", "判定と運用", "予備審査の結果をどう扱うか。")}
  <table class="bd">
    <thead><tr><th>判定</th><th class="num">総合点</th><th>予備審査での扱い</th></tr></thead>
    <tbody>{bands}</tbody>
  </table>
  <h4 style="margin-top:28px">同点時のタイブレーク順</h4>
  <ol class="tb">{"".join(f"<li>{E(t)} のレベルが高いほうを上位</li>" for t in TIEBREAK)}</ol>
  <div class="note">
    <b>予備審査の位置づけ。</b>
    S・A判定は人手審査へ自動送付、B判定は事務局が拾い上げを検討、C判定は見送りを基本とします。
    AIは応募資料に書かれていることだけで採点し、書かれていない良さを推測して加点しません。
    情報不足でレベルを下げた観点は出力に記録されるため、資料の書き方が原因で沈んだ応募は事務局が確認できます。
  </div>
</section>

<footer>
  {E(META['title'])}　／　作成日 {META['built']}<br>
  元データ：{E(META['source'])}<br>
  本資料・ルーブリック・採点シート・AI審査プロンプトは、いずれも同一の定義ファイルから自動生成しています。観点や配点を変更した場合は、4つすべてに同時に反映されます。
</footer>

</div>
"""

if __name__ == "__main__":
    import pathlib
    pathlib.Path("審査員向け説明資料.html").write_text(HTML, encoding="utf-8")
    print(f"{len(HTML)} chars")
