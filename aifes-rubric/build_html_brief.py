# -*- coding: utf-8 -*-
"""rubric_data.py から内部メンバー向けの採点実務ブリーフ（HTML）を生成する。

審査員向け説明資料（build_html.py）が「合意を取るための資料」なのに対し、
こちらは「実際に採点を回す人が手元に置く早見表」。
"""
import html
from rubric_data import CRITERIA, JUDGES, FLAGS, BANDS, TIEBREAK, META, WEIGHTS, STEP

E = html.escape
LEVELS = [5, 4, 3, 2, 1]
TOTAL = sum(WEIGHTS)
N_JUDGES = len(JUDGES)

# 全観点を同じレベルでつけたときの総合点（キャリブレーション用）
def flat(lv):
    return sum(lv / 5 * w for w in WEIGHTS)


def band_of(score):
    for cut, lab, _ in BANDS:
        if score >= cut:
            return lab
    return BANDS[-1][1]


# ---------------------------------------------------------------- 観点バー
sticky = "".join(
    f'<a href="#{c["id"]}" class="sx"><b>{c["id"]}</b>'
    f'<span>{E(c["short"])}</span><i>{c["weight"]}</i></a>'
    for c in CRITERIA)

# ---------------------------------------------------------------- 観点サマリ表
summary = "".join(
    f'<tr><td class="cid"><a href="#{c["id"]}">{c["id"]}</a></td>'
    f'<th scope="row">{E(c["name"])}</th>'
    f'<td class="qq">{E(c["question"])}</td>'
    f'<td class="wt">{c["weight"]}</td></tr>'
    for c in CRITERIA)

# ---------------------------------------------------------------- 観点リファレンス
refs = []
for c in CRITERIA:
    caps = [f for f in FLAGS if c["id"] in f["cap"]]
    cap_note = ("".join(
        f'<li><b>{f["id"]}</b> {E(f["name"])} に該当 → <em>レベル{f["cap"][c["id"]]}以下</em></li>'
        for f in caps))
    cap_block = (f'<div class="capbox"><h5>この観点にかかる上限</h5><ul>{cap_note}</ul></div>'
                 if caps else "")
    rows = "".join(
        f'<tr class="{"top" if n == 5 else ""}"><td class="lv">{n}</td>'
        f'<td class="lvd">{E(t)}</td>'
        f'<td class="lvp">{int(n / 5 * c["weight"])}</td></tr>'
        for n, t in zip(LEVELS, c["levels"]))
    refs.append(f"""
<article class="ref" id="{c['id']}">
  <header>
    <span class="rid">{c['id']}</span>
    <div class="rt"><h3>{E(c['name'])}</h3><p>{E(c['question'])}</p></div>
    <span class="rw">{c['weight']}<i>点</i></span>
  </header>
  <div class="rbody">
    <table class="lvt">
      <thead><tr><th>Lv</th><th>この状態なら該当</th><th>得点</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    {cap_block}
  </div>
</article>""")

# ---------------------------------------------------------------- フラグ
flagcards = "".join(f"""
<article class="fg">
  <div class="fgh"><span class="fgid">{f['id']}</span><h3>{E(f['name'])}</h3></div>
  <p class="fgd">{E(f['detect'])}</p>
  <p class="fgc">{"　".join(f"{cid} を <b>レベル{cap}以下</b>に" for cid, cap in f['cap'].items())}</p>
</article>""" for f in FLAGS)

# ---------------------------------------------------------------- 判定
bandrows = "".join(
    f'<tr><td class="bl b-{lab}">{lab}</td>'
    f'<td class="num">{cut}〜</td><td>{E(desc)}</td></tr>'
    if cut else
    f'<tr><td class="bl b-{lab}">{lab}</td><td class="num">〜{BANDS[-2][0] - 1}</td><td>{E(desc)}</td></tr>'
    for cut, lab, desc in BANDS)

# 早見表：配点別のレベル→得点
wsets = sorted({c["weight"] for c in CRITERIA}, reverse=True)
quick_head = "".join(f'<th class="num">Lv{n}</th>' for n in LEVELS)
quick_rows = "".join(
    '<tr><th scope="row">配点{w}点<span>{names}</span></th>{cells}</tr>'.format(
        w=w,
        names=" ".join(c["id"] for c in CRITERIA if c["weight"] == w),
        cells="".join(f'<td class="num">{int(n / 5 * w)}</td>' for n in LEVELS))
    for w in wsets)

calib = "".join(
    f'<tr><th scope="row">全観点をレベル{n}でつけた場合</th>'
    f'<td class="num big">{int(flat(n))}</td>'
    f'<td class="bl b-{band_of(flat(n))}">{band_of(flat(n))}</td></tr>'
    for n in LEVELS)

STEPS = [
    ("応募資料を1件ずつAIに渡す",
     "プロンプトは <code>AI予備審査プロンプト.md</code>（Excelの 05 シートにも同じ本文あり）。"
     "件ごとに書き換える必要はない。応募資料だけを差し替える。"),
    ("AIがJSONで返す",
     "6観点のレベル・根拠の原文引用・そのレベルにした理由・前提フラグの該当・強み弱み・"
     "「人手審査で確認すべき点」「資料に情報が不足している観点」が入る。"),
    ("採点シート（03）に転記する",
     "青字のセルだけ埋める。観点レベル D〜I、前提フラグ S〜V、AI所見 X。"
     "加重得点・総合点・判定・順位は自動で出る。"),
    ("W列「上限チェック」を確認する",
     "「上限超過」と出たら、フラグと入力レベルが矛盾している。該当観点のレベルを上限まで下げる。"
     "ここを飛ばすと、前提フラグが効かないまま順位が出る。"),
    ("S・A判定を人手審査へ回す",
     "B判定は事務局で拾い上げを検討、C判定は見送りが基本。"
     "「資料に情報が不足している観点」が付いた応募は、実力ではなく書き方が原因で沈んでいないか必ず目視する。"),
]
steps = "".join(f"""
<li><div class="stn">{i}</div><div class="stb"><h3>{E(t)}</h3><p>{d}</p></div></li>"""
                for i, (t, d) in enumerate(STEPS, 1))

DONTS = [
    ("資料に書いていない良さを補わない",
     "AIにも人にも共通。情報が足りない観点はレベルを下げ、記録に残す。推測で埋めると審査員に説明できなくなる。"),
    ("「AIを導入した」は加点材料ではない",
     "ツール名やPoCの実施そのものは評価しない。業務・組織・人がどう変わったかだけを見る。"),
    ("生産性の数値の大きさで決めない",
     "時短率や削減時間は前提であって差別化要因ではない。数字が大きいというだけで高いレベルをつけない。"),
    ("役職の高さを採点に持ち込まない",
     "採点対象は取り組みそのもの。配点も役職で重み付けしていないので、ここで持ち込むと設計が崩れる。"),
    ("迷ったら低いほうをつける",
     "上のレベルの記述を<b>すべて</b>満たしていなければ、そのレベルには到達していない。"),
    ("予備審査で決着させない",
     "これは足切りと順位づけの一次スクリーニング。最終決定は審査員12名による人手審査で行う。"),
]
donts = "".join(f'<li><h3>{E(t)}</h3><p>{d}</p></li>' for t, d in DONTS)

tie = "".join(f"<li>{E(t)}</li>" for t in TIEBREAK)

CSS = """
*{box-sizing:border-box}
:root{
  --paper:#F4F6F9; --card:#FFFFFF; --ink:#141F33; --ink2:#3C4B66; --mute:#6C7C97;
  --line:#D7DEE9; --line2:#E9EEF5; --sunk:#EDF1F6;
  --navy:#1F3864; --navy2:#2E4E86; --gold:#9C7418; --gold-s:#F6EFDD;
  --ok:#2C6B4F; --ok-s:#E3F0E8; --warn:#9A5B12; --warn-s:#FBEEDC; --bad:#8E3838;
  --shadow:0 1px 2px rgba(20,31,51,.05),0 6px 20px -12px rgba(20,31,51,.2);
  --disp:"Hiragino Mincho ProN","Yu Mincho",YuMincho,"Noto Serif JP",serif;
  --body:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic","Noto Sans JP","Meiryo",sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --paper:#0C1320; --card:#141E2F; --ink:#E7ECF4; --ink2:#B5C1D4; --mute:#8494AD;
  --line:#28344A; --line2:#1D2839; --sunk:#101A29;
  --navy:#8FB0E6; --navy2:#A9C4F0; --gold:#D8B25A; --gold-s:#2B2416;
  --ok:#6FBF95; --ok-s:#16281F; --warn:#D9A05B; --warn-s:#2B2013; --bad:#D98080;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 6px 22px -14px rgba(0,0,0,.75);
}}
:root[data-theme="dark"]{
  --paper:#0C1320; --card:#141E2F; --ink:#E7ECF4; --ink2:#B5C1D4; --mute:#8494AD;
  --line:#28344A; --line2:#1D2839; --sunk:#101A29;
  --navy:#8FB0E6; --navy2:#A9C4F0; --gold:#D8B25A; --gold-s:#2B2416;
  --ok:#6FBF95; --ok-s:#16281F; --warn:#D9A05B; --warn-s:#2B2013; --bad:#D98080;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 6px 22px -14px rgba(0,0,0,.75);
}
:root[data-theme="light"]{
  --paper:#F4F6F9; --card:#FFFFFF; --ink:#141F33; --ink2:#3C4B66; --mute:#6C7C97;
  --line:#D7DEE9; --line2:#E9EEF5; --sunk:#EDF1F6;
  --navy:#1F3864; --navy2:#2E4E86; --gold:#9C7418; --gold-s:#F6EFDD;
  --ok:#2C6B4F; --ok-s:#E3F0E8; --warn:#9A5B12; --warn-s:#FBEEDC; --bad:#8E3838;
  --shadow:0 1px 2px rgba(20,31,51,.05),0 6px 20px -12px rgba(20,31,51,.2);
}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);
  font-size:14px;line-height:1.8;-webkit-font-smoothing:antialiased;
  font-feature-settings:"palt" 1}
.wrap{max-width:900px;margin:0 auto;padding:0 22px 88px}
section{margin-top:56px}
h2{font-family:var(--disp);font-size:22px;margin:0;font-weight:600;line-height:1.4;
  letter-spacing:.02em;text-wrap:balance}
.sh{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;
  border-bottom:2px solid var(--navy);padding-bottom:10px;margin-bottom:22px}
.sn{font-family:var(--mono);font-size:11px;font-weight:700;color:var(--gold);
  letter-spacing:.16em;flex:none}
.ss{margin:0;font-size:12.5px;color:var(--mute);flex:1 1 240px;line-height:1.7}
code{font-family:var(--mono);font-size:.9em;background:var(--sunk);padding:1px 5px;
  border-radius:2px;border:1px solid var(--line2)}

/* hero */
.hero{background:#1B3054;border-bottom:3px solid var(--gold)}
:root[data-theme="dark"] .hero{background:#111B2C}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .hero{background:#111B2C}}
:root[data-theme="light"] .hero{background:#1B3054}
.hin{max-width:900px;margin:0 auto;padding:38px 22px 30px}
.eb{font-family:var(--mono);font-size:10.5px;letter-spacing:.18em;color:#D6BB7A;
  margin:0 0 12px;font-weight:700}
.hero h1 em{font-style:normal;font-family:var(--body);font-size:14px;font-weight:400;
  color:#B9C9E2;margin-left:12px;letter-spacing:.04em;white-space:nowrap}
.hero h1{font-family:var(--disp);font-size:clamp(24px,3.6vw,32px);margin:0 0 12px;
  color:#fff;font-weight:600;line-height:1.4;text-wrap:balance}
.hero p{margin:0;color:#B9C9E2;font-size:13.5px;max-width:62ch;line-height:1.95}
.kpi{display:flex;gap:26px;margin-top:24px;flex-wrap:wrap}
.kpi div{line-height:1.3}
.kpi b{display:block;font-family:var(--mono);font-size:24px;color:#E8C87C;
  font-variant-numeric:tabular-nums}
.kpi span{font-size:10.5px;color:#9FB4D2;letter-spacing:.06em}

/* sticky 観点バー */
.bar{position:sticky;top:0;z-index:20;background:var(--card);
  border-bottom:1px solid var(--line);box-shadow:var(--shadow)}
.bin{max-width:900px;margin:0 auto;padding:8px 22px;display:flex;gap:6px;
  overflow-x:auto;scrollbar-width:thin}
.sx{flex:1 0 auto;min-width:104px;display:grid;grid-template-columns:auto 1fr auto;
  align-items:center;gap:6px;text-decoration:none;padding:6px 9px;border-radius:2px;
  border:1px solid var(--line2);background:var(--sunk)}
.sx:hover{border-color:var(--gold)}
.sx b{font-family:var(--mono);font-size:10px;color:var(--gold);font-weight:700}
.sx span{font-size:11.5px;color:var(--ink);font-weight:700;white-space:nowrap}
.sx i{font-family:var(--mono);font-style:normal;font-size:13px;font-weight:700;
  color:var(--navy);font-variant-numeric:tabular-nums}

/* テーブル共通 */
table{border-collapse:collapse;width:100%;background:var(--card);font-size:13px;
  border:1px solid var(--line);box-shadow:var(--shadow)}
th,td{border-bottom:1px solid var(--line2);padding:8px 12px;text-align:left;
  vertical-align:top}
thead th{background:var(--sunk);font-size:10.5px;letter-spacing:.08em;color:var(--mute);
  font-weight:700;white-space:nowrap}
tbody tr:last-child th,tbody tr:last-child td{border-bottom:none}
.num{font-family:var(--mono);text-align:right;font-variant-numeric:tabular-nums}
.tsc{overflow-x:auto}

/* 観点サマリ */
table.sum td.cid a{font-family:var(--mono);font-weight:700;color:var(--gold);
  text-decoration:none;font-size:12px}
table.sum th[scope="row"]{font-weight:700;white-space:nowrap}
table.sum .qq{color:var(--mute);font-size:12px;line-height:1.7}
table.sum .wt{font-family:var(--mono);font-weight:700;font-size:17px;text-align:right;
  color:var(--navy);white-space:nowrap;font-variant-numeric:tabular-nums}
table.sum tfoot td{background:var(--sunk);font-weight:700}

/* 手順 */
ol.steps{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:2px}
ol.steps li{display:grid;grid-template-columns:44px 1fr;gap:14px;background:var(--card);
  border:1px solid var(--line);border-bottom:none;padding:14px 18px 14px 14px}
ol.steps li:first-child{border-radius:3px 3px 0 0}
ol.steps li:last-child{border-bottom:1px solid var(--line);border-radius:0 0 3px 3px}
.stn{font-family:var(--mono);font-weight:700;font-size:15px;color:#fff;background:var(--navy);
  width:30px;height:30px;display:grid;place-items:center;border-radius:50%;margin-top:2px}
:root[data-theme="dark"] .stn{color:#0C1320}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .stn{color:#0C1320}}
.stb h3{margin:0 0 3px;font-size:14.5px;font-weight:700}
.stb p{margin:0;font-size:12.5px;color:var(--ink2);line-height:1.8}

/* 観点リファレンス */
.ref{background:var(--card);border:1px solid var(--line);border-radius:3px;
  margin-bottom:14px;box-shadow:var(--shadow);scroll-margin-top:64px;overflow:hidden}
.ref>header{display:flex;align-items:center;gap:12px;padding:13px 18px;
  background:var(--sunk);border-bottom:1px solid var(--line)}
.rid{font-family:var(--mono);font-weight:700;font-size:12px;color:#fff;background:var(--navy);
  padding:3px 8px;border-radius:2px;flex:none}
:root[data-theme="dark"] .rid{color:#0C1320}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .rid{color:#0C1320}}
.rt{flex:1 1 auto;min-width:0}
.rt h3{margin:0;font-family:var(--disp);font-size:17px;font-weight:600;line-height:1.4}
.rt p{margin:1px 0 0;font-size:12px;color:var(--gold);line-height:1.6}
.rw{font-family:var(--mono);font-size:24px;font-weight:700;color:var(--navy);flex:none;
  font-variant-numeric:tabular-nums}
.rw i{font-style:normal;font-size:11px;color:var(--mute);margin-left:1px}
.rbody{padding:0}
table.lvt{border:none;box-shadow:none}
table.lvt thead th{background:transparent;border-bottom:1px solid var(--line2);
  padding:7px 14px}
table.lvt thead th:last-child,table.lvt td.lvp{text-align:right}
table.lvt td{padding:9px 14px}
td.lv{font-family:var(--mono);font-weight:700;width:34px;text-align:center;
  color:var(--mute);font-size:12px}
tr.top td.lv{color:var(--gold)}
td.lvd{font-size:12.5px;line-height:1.75;color:var(--ink2)}
tr.top td.lvd{color:var(--ink)}
td.lvp{font-family:var(--mono);width:52px;color:var(--navy);font-weight:700;
  font-variant-numeric:tabular-nums}
.capbox{background:var(--warn-s);border-top:1px solid var(--line2);padding:10px 14px}
.capbox h5{margin:0 0 4px;font-size:10.5px;letter-spacing:.08em;color:var(--warn);
  font-weight:700}
.capbox ul{margin:0;padding-left:16px;font-size:12px;line-height:1.8;color:var(--ink2)}
.capbox b{font-family:var(--mono);color:var(--warn)}
.capbox em{font-style:normal;font-weight:700;color:var(--warn)}

/* フラグ */
.fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.fg{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--warn);
  border-radius:3px;padding:14px 16px;box-shadow:var(--shadow)}
.fgh{display:flex;align-items:center;gap:9px;margin-bottom:7px}
.fgid{font-family:var(--mono);font-weight:700;font-size:11px;color:var(--warn);
  background:var(--warn-s);padding:2px 7px;border-radius:2px}
.fg h3{margin:0;font-size:14px;font-weight:700}
.fgd{margin:0 0 8px;font-size:12.5px;color:var(--ink2);line-height:1.75}
.fgc{margin:0;font-size:12px;color:var(--warn);font-weight:700;line-height:1.7;
  border-top:1px dashed var(--line);padding-top:7px}
.fgc b{font-family:var(--mono)}

/* 判定 */
.bl{font-family:var(--mono);font-weight:700;font-size:16px;width:48px;text-align:center}
.b-S{color:var(--gold)} .b-A{color:var(--ok)} .b-B{color:var(--warn)} .b-C{color:var(--mute)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}
/* min-width:auto だとテーブルの最小幅がトラックを押し広げ、.tsc の横スクロールが効かない */
.two>div{min-width:0}
h4{font-size:11px;letter-spacing:.1em;color:var(--mute);margin:0 0 9px;font-weight:700}
table.qk th[scope="row"]{white-space:nowrap;font-weight:700;font-size:12.5px}
table.qk th,table.qk td{padding:8px 9px}
table.qk th[scope="row"] span{display:block;font-family:var(--mono);font-size:10px;
  color:var(--mute);font-weight:400;letter-spacing:.04em}
table.qk td{font-size:14px;font-weight:700;color:var(--navy)}
table.cb .big{font-size:17px;font-weight:700;color:var(--navy)}
ol.tie{margin:10px 0 0;padding-left:19px;font-size:12.5px;color:var(--ink2);line-height:1.95}
ol.tie li::marker{color:var(--gold);font-family:var(--mono);font-weight:700}

/* やってはいけない */
ul.dont{list-style:none;margin:0;padding:0;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px}
ul.dont li{background:var(--card);border:1px solid var(--line);border-radius:3px;
  padding:13px 16px;box-shadow:var(--shadow);position:relative;padding-left:38px}
ul.dont li::before{content:"×";position:absolute;left:15px;top:12px;font-family:var(--mono);
  font-weight:700;color:var(--bad);font-size:14px}
ul.dont li:last-child::before,ul.dont li:nth-last-child(2)::before{content:"！";color:var(--gold)}
ul.dont h3{margin:0 0 4px;font-size:13.5px;font-weight:700;line-height:1.5}
ul.dont p{margin:0;font-size:12px;color:var(--ink2);line-height:1.75}

.note{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--navy);
  padding:14px 18px;font-size:12.5px;color:var(--ink2);line-height:1.85;margin-top:18px}
.note b{color:var(--ink)}
footer{margin-top:64px;padding-top:18px;border-top:1px solid var(--line);
  font-size:11px;color:var(--mute);line-height:1.85}
a{color:var(--navy2)}
a:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
@media (max-width:720px){
  .two{grid-template-columns:1fr}
  .bar{position:static}
  .ref>header{flex-wrap:wrap}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media print{
  .bar{display:none}
  body{background:#fff;font-size:10.5pt}
  .ref,.fg,ol.steps li,ul.dont li,table{box-shadow:none;break-inside:avoid}
  section{margin-top:26px}
  .hero{background:#1B3054!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
"""

HTML = f"""<title>AIFES 2026 グランドフィナーレ 予備審査 採点ブリーフ（内部用）</title>
<style>{CSS}</style>
<div class="hero">
  <div class="hin">
    <p class="eb">AIFES 2026 ／ GRAND FINALE ／ 予備審査</p>
    <h1>採点ブリーフ<em>内部メンバー用</em></h1>
    <p>審査員{N_JUDGES}名のコメントを6観点に集約したルーブリックで、グランドフィナーレの予備審査を行います。
       この資料は、実際に採点を回すメンバーが手元に置くための早見表です。
       ルーブリックの成り立ちや配点の根拠は、審査員向け説明資料のほうに載せています。</p>
    <div class="kpi">
      <div><b>{N_JUDGES}</b><span>審査員コメント</span></div>
      <div><b>{len(CRITERIA)}</b><span>評価観点</span></div>
      <div><b>{TOTAL}</b><span>点満点</span></div>
      <div><b>{len(FLAGS)}</b><span>前提フラグ</span></div>
      <div><b>{" / ".join(b[1] for b in BANDS)}</b><span>判定</span></div>
    </div>
  </div>
</div>

<nav class="bar"><div class="bin">{sticky}</div></nav>

<div class="wrap">

<section>
  <div class="sh"><span class="sn">01</span><h2>採点する6つの観点</h2>
    <p class="ss">配点は{STEP}点刻み・合計{TOTAL}点。各観点をレベル1〜5でつけ、レベル ÷ 5 × 配点 が得点になります。</p></div>
  <div class="tsc"><table class="sum">
    <thead><tr><th>ID</th><th>観点</th><th>何を見るか</th><th style="text-align:right">配点</th></tr></thead>
    <tbody>{summary}</tbody>
    <tfoot><tr><td></td><td>合計</td><td></td><td class="wt">{TOTAL}</td></tr></tfoot>
  </table></div>
  <div class="note">
    <b>この6観点で、審査員{N_JUDGES}名全員の観点がカバーされています。</b>
    そのため、審査員ごとに採点をやり直す必要はありません。1件につき1回の採点で完了します。
    配点は「何名がその観点に言及したか」から機械的に算出しており、役職による重み付けは行っていません。
  </div>
</section>

<section>
  <div class="sh"><span class="sn">02</span><h2>採点の手順</h2>
    <p class="ss">1件あたりの流れ。ステップ4を飛ばすと前提フラグが効かないまま順位が出ます。</p></div>
  <ol class="steps">{steps}</ol>
</section>

<section>
  <div class="sh"><span class="sn">03</span><h2>観点別 採点リファレンス</h2>
    <p class="ss">レベルは上から5〜1。右端はその観点で入る得点です。迷ったら低いほうをつけてください。</p></div>
  {"".join(refs)}
</section>

<section>
  <div class="sh"><span class="sn">04</span><h2>前提フラグ</h2>
    <p class="ss">加点ではなく上限です。該当したら、その観点は指定レベル以上をつけられません。</p></div>
  <div class="fgrid">{flagcards}</div>
  <div class="note">
    <b>なぜ加点ではなく上限なのか。</b>
    「生産性向上は企業として取り組むべき前提」「何をAIで実現したかよりも文化」というのが審査員の言葉でした。
    これらを加点材料にすると、数値の大きい応募がそのまま上位に来てしまいます。
    採点シートの <code>W列 上限チェック</code> が、フラグと入力レベルの矛盾を自動で検出します。
  </div>
</section>

<section>
  <div class="sh"><span class="sn">05</span><h2>判定と得点の目安</h2>
    <p class="ss">総合点から判定が自動で決まります。同点時は下記の順で比較します。</p></div>
  <div class="tsc"><table class="bd">
    <thead><tr><th>判定</th><th style="text-align:right">総合点</th><th>扱い</th></tr></thead>
    <tbody>{bandrows}</tbody>
  </table></div>

  <div class="two" style="margin-top:22px">
    <div>
      <h4>レベル → 得点 早見表</h4>
      <div class="tsc"><table class="qk">
        <thead><tr><th>観点</th>{quick_head}</tr></thead>
        <tbody>{quick_rows}</tbody>
      </table></div>
    </div>
    <div>
      <h4>総合点のキャリブレーション</h4>
      <div class="tsc"><table class="cb">
        <thead><tr><th>つけ方</th><th style="text-align:right">総合点</th><th>判定</th></tr></thead>
        <tbody>{calib}</tbody>
      </table></div>
    </div>
  </div>

  <h4 style="margin-top:26px">同点時のタイブレーク順</h4>
  <ol class="tie">{tie}</ol>
  <div class="note">
    <b>配点の大小では順位が決まりません。</b>
    {STEP}点刻みに丸めた結果、{"・".join(c["id"] for c in CRITERIA if c["weight"] == max(WEIGHTS))} が同じ{max(WEIGHTS)}点で並びます。
    同点が出た場合は、書面から実態を読み取りやすい観点を優先してください。
    C6（当事者性と熱量）は当日のプレゼンで印象が変わりうるため、最後に置いています。
  </div>
</section>

<section>
  <div class="sh"><span class="sn">06</span><h2>採点で気をつけること</h2>
    <p class="ss">AIに渡すプロンプトにも同じ制約を入れていますが、転記・確認の段階で崩れやすいところです。</p></div>
  <ul class="dont">{donts}</ul>
</section>

<footer>
  {E(META['title'])}　内部メンバー向け採点ブリーフ　／　作成日 {META['built']}<br>
  関連ファイル：<code>AIFES2026_グランドフィナーレ_AI予備審査ルーブリック.xlsx</code>（ルーブリック・採点シート・元データ）、
  <code>AI予備審査プロンプト.md</code>（AIに渡す本文）、審査員向け説明資料（配点の導出と審査員別の対応表）<br>
  元データ：{E(META['source'])}　／　本資料は他の成果物と同一の定義ファイルから自動生成しています。
</footer>

</div>
"""

if __name__ == "__main__":
    import pathlib
    pathlib.Path("採点ブリーフ_内部用.html").write_text(HTML, encoding="utf-8")
    print(f"{len(HTML)} chars")
