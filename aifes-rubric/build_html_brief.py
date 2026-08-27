# -*- coding: utf-8 -*-
"""rubric_data.py から内部メンバー向けの採点実務ブリーフ（HTML）を生成する。

審査員向け説明資料（build_html.py）が「合意を取るための資料」なのに対し、
こちらは「実際に採点を回す人が手元に置く早見表」。

配色は6観点それぞれに固有の色を割り当て、サイドバー・マトリクス・
リファレンスカード・チップまで一貫させている（C4なら常にアンバー）。
6色はライト／ダーク両テーマで、地色・淡色地の両方に対して
コントラスト比 4.5 以上を確認済み。
"""
import html
from rubric_data import CRITERIA, JUDGES, FLAGS, BANDS, TIEBREAK, META, WEIGHTS, STEP

E = html.escape
LEVELS = [5, 4, 3, 2, 1]
TOTAL = sum(WEIGHTS)
N_JUDGES = len(JUDGES)
J = {j["no"]: j for j in JUDGES}

# 観点の並び順に色を割り当てる（観点が増えても循環する）
N_HUE = 6
def hue(c):
    return f"c{CRITERIA.index(c) % N_HUE + 1}"


def marks_of(judge_no, crit):
    """その審査員がこの観点に寄与している印。◎＝グランドフィナーレコメント由来。"""
    ms = [m for jn, m, _ in crit["sources"] if jn == judge_no]
    if not ms:
        return None
    return "◎" if "◎" in ms else "○"


def emphasis_axes(judge_no):
    """その審査員が◎で重視している観点。"""
    return [c for c in CRITERIA
            if any(jn == judge_no and m == "◎" for jn, m, _ in c["sources"])]


def judges_of(crit, mark="◎"):
    return [J[jn] for jn, m, _ in crit["sources"] if m == mark]


def flat(lv):
    return sum(lv / 5 * w for w in WEIGHTS)


def band_of(score):
    for cut, lab, _ in BANDS:
        if score >= cut:
            return lab
    return BANDS[-1][1]


# ---------------------------------------------------------------- 観点バー
sticky = "".join(
    f'<a href="#{c["id"]}" class="sx {hue(c)}"><b>{c["id"]}</b>'
    f'<span>{E(c["short"])}</span><i>{c["weight"]}</i></a>'
    for c in CRITERIA)

# 6観点の配点を色で示す帯
ribbon = "".join(
    f'<i class="{hue(c)}" style="flex:{c["weight"]}" title="{c["id"]} {E(c["short"])} {c["weight"]}点"></i>'
    for c in CRITERIA)

# ---------------------------------------------------------------- 観点サマリ表
summary = "".join(
    f'<tr class="{hue(c)}"><td class="cid"><a href="#{c["id"]}">{c["id"]}</a></td>'
    f'<th scope="row">{E(c["name"])}</th>'
    f'<td class="qq">{E(c["question"])}</td>'
    f'<td class="wt">{c["weight"]}</td></tr>'
    for c in CRITERIA)

# ---------------------------------------------------------------- 観点リファレンス
refs = []
for c in CRITERIA:
    caps = [f for f in FLAGS if c["id"] in f["cap"]]
    cap_block = ""
    if caps:
        items = "".join(
            f'<li><b>{f["id"]}</b> {E(f["name"])} に該当 → <em>レベル{f["cap"][c["id"]]}以下</em></li>'
            for f in caps)
        cap_block = f'<div class="capbox"><h5>この観点にかかる上限</h5><ul>{items}</ul></div>'
    rows = "".join(
        f'<tr class="{"top" if n == 5 else ""}"><td class="lv"><span>{n}</span></td>'
        f'<td class="lvd">{E(t)}</td>'
        f'<td class="lvp">{int(n / 5 * c["weight"])}</td></tr>'
        for n, t in zip(LEVELS, c["levels"]))
    emph = judges_of(c, "◎")
    also = [j for j in judges_of(c, "○") if j not in emph]
    who = ('<div class="rwho"><span class="wl">重視</span>'
           + "".join(f'<a href="#jm" class="jt jd">{E(j["name"])}</a>' for j in emph)
           + "".join(f'<a href="#jm" class="jt jo">{E(j["name"])}</a>' for j in also)
           + "</div>")
    refs.append(f"""
<article class="ref {hue(c)}" id="{c['id']}">
  <header>
    <span class="rid">{c['id']}</span>
    <div class="rt"><h3>{E(c['name'])}</h3><p>{E(c['question'])}</p></div>
    <span class="rw">{c['weight']}<i>点</i></span>
  </header>
  {who}
  <div class="rbody">
    <table class="lvt">
      <thead><tr><th>Lv</th><th>この状態なら該当</th><th>得点</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    {cap_block}
  </div>
</article>""")

# ---------------------------------------------------------------- 審査員別 重視観点
mxhead = "".join(
    f'<th class="{hue(c)}"><a href="#{c["id"]}"><b>{c["id"]}</b>'
    f'<span>{E(c["short"])}</span><i>{c["weight"]}点</i></a></th>' for c in CRITERIA)
mxrows = []
for j in JUDGES:
    cells = ""
    for c in CRITERIA:
        mk = marks_of(j["no"], c)
        if mk == "◎":
            cells += f'<td class="d {hue(c)}"><span>◎</span></td>'
        elif mk == "○":
            cells += f'<td class="o {hue(c)}"><span>○</span></td>'
        else:
            cells += "<td></td>"
    mxrows.append(
        f'<tr><th scope="row"><b>{E(j["name"])}</b><i>{E(j["title"])}</i></th>{cells}</tr>')
mxfoot = "".join(
    f'<td class="tw {hue(c)}"><b>{len(judges_of(c, "◎"))}</b><span>名</span></td>'
    for c in CRITERIA)

quotes = "".join(f"""
<article class="qt">
  <div class="qh"><h3>{E(j['name'])}</h3><p>{E(j['title'])}</p></div>
  <blockquote>{E(j['gf'])}</blockquote>
  <div class="qc">{"".join(
      f'<a href="#{c["id"]}" class="qchip {hue(c)}">{c["id"]} {E(c["short"])}</a>'
      for c in emphasis_axes(j['no']))}</div>
</article>""" for j in JUDGES)

# ---------------------------------------------------------------- フラグ
flagcards = "".join(f"""
<article class="fg">
  <div class="fgh"><span class="fgid">{f['id']}</span><h3>{E(f['name'])}</h3></div>
  <p class="fgd">{E(f['detect'])}</p>
  <p class="fgc">{"　".join(f"{cid} を <b>レベル{cap}以下</b>に" for cid, cap in f['cap'].items())}</p>
</article>""" for f in FLAGS)

# ---------------------------------------------------------------- 判定
bandrows = "".join(
    f'<tr><td class="bl b-{lab}"><span>{lab}</span></td>'
    f'<td class="num">{cut}〜</td><td>{E(desc)}</td></tr>'
    if cut else
    f'<tr><td class="bl b-{lab}"><span>{lab}</span></td>'
    f'<td class="num">〜{BANDS[-2][0] - 1}</td><td>{E(desc)}</td></tr>'
    for cut, lab, desc in BANDS)

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
    f'<td class="bl b-{band_of(flat(n))}"><span>{band_of(flat(n))}</span></td></tr>'
    for n in LEVELS)

STEPS = [
    ("応募資料を1件ずつAIに渡す",
     "プロンプトは <code>AI予備審査プロンプト.md</code>（Excelの 06 シートにも同じ本文あり）。"
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
donts = "".join(
    f'<li class="{"warn" if i >= len(DONTS) - 1 else "no"}"><h3>{E(t)}</h3><p>{d}</p></li>'
    for i, (t, d) in enumerate(DONTS))

tie = "".join(f"<li>{E(t)}</li>" for t in TIEBREAK)

# ==================================================================
# 図解。すべて rubric_data の値から座標を計算しているので、観点や
# 配点を変えると図も追随する。
# ==================================================================
ARROW = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" '
         'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
         '<path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>')


def fig_weights():
    """配点の構成（100点の内訳を面積で示す）"""
    W, BX, BW, BY, BH = 880, 4, 872, 12, 52
    segs, names, x = [], [], BX
    for c in CRITERIA:
        w = c["weight"] / TOTAL * BW
        segs.append(
            f'<rect class="{hue(c)}" x="{x:.1f}" y="{BY}" width="{w:.1f}" height="{BH}" '
            f'style="fill:var(--c)"/>'
            f'<text x="{x + w / 2:.1f}" y="{BY + 21}" class="sg-id">{c["id"]}</text>'
            f'<text x="{x + w / 2:.1f}" y="{BY + 42}" class="sg-w">{c["weight"]}点</text>')
        names.append(
            f'<text x="{x + w / 2:.1f}" y="{BY + BH + 20}" class="sg-n">{E(c["short"])}</text>')
        x += w
    return f"""
<figure class="dg">
  <svg viewBox="0 0 {W} {BY + BH + 30}" role="img"
       aria-label="100点の配点の内訳。{'、'.join(f'{c["id"]} {c["short"]} {c["weight"]}点' for c in CRITERIA)}。">
    <clipPath id="wclip"><rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="9"/></clipPath>
    <g clip-path="url(#wclip)">{"".join(segs)}</g>
    {"".join(names)}
  </svg>
  <figcaption>面積がそのまま配点。C2 組織浸透 と C4 波及と視座 に重みが寄っているのは、
    その観点を挙げた役員が多かったためです。</figcaption>
</figure>"""


def fig_flow():
    """採点フロー。差し戻しの経路と、判定による3分岐がこの図の要点。"""
    boxes = [
        (6, 104, "応募資料", "1件ずつ"),
        (136, 152, "AIが採点", "プロンプトは固定"),
        (316, 152, "採点シートに転記", "自動で加重・集計"),
    ]
    bs = "".join(
        f'<rect x="{x}" y="105" width="{w}" height="46" rx="9" class="bx"/>'
        f'<text x="{x + w / 2}" y="{123 if sub else 132}" class="bt">{t}</text>'
        + (f'<text x="{x + w / 2}" y="140" class="bs">{sub}</text>' if sub else "")
        for x, w, t, sub in boxes)
    arrows = "".join(
        f'<line x1="{a}" y1="128" x2="{b}" y2="128" class="ln" marker-end="url(#ah)"/>'
        for a, b in ((110, 132), (288, 312), (468, 496)))

    outs = [
        (40, "S・A", "人手審査へ回す", "b5"),
        (106, "B", "事務局で拾い上げを検討", "b4"),
        (172, "C", "見送り", "bm"),
    ]
    ob = "".join(
        f'<rect x="700" y="{y}" width="176" height="44" rx="9" class="bx {cl}"/>'
        f'<text x="716" y="{y + 27}" class="bl2 {cl}">{lab}</text>'
        f'<text x="{716 + (34 if len(lab) < 3 else 58)}" y="{y + 27}" class="bs2">{txt}</text>'
        for y, lab, txt, cl in outs)
    fan = ('<line x1="650" y1="128" x2="678" y2="128" class="ln"/>'
           '<line x1="678" y1="62" x2="678" y2="194" class="ln"/>'
           + "".join(f'<line x1="678" y1="{y + 22}" x2="696" y2="{y + 22}" '
                     f'class="ln" marker-end="url(#ah)"/>' for y, *_ in outs))

    return f"""
<figure class="dg">
  <svg viewBox="0 0 890 232" role="img"
       aria-label="採点フロー。応募資料をAIが採点しJSONを採点シートに転記、上限チェックで超過なら該当観点のレベルを下げて転記に戻り、通れば判定に応じてSとAは人手審査、Bは拾い上げ検討、Cは見送り。">
    {ARROW}
    {bs}{arrows}
    <polygon points="575,82 650,128 575,174 500,128" class="dia"/>
    <text x="575" y="124" class="bt dia-t">上限チェック</text>
    <text x="575" y="141" class="bs dia-t">W列</text>
    <path d="M575,82 L575,58 L392,58 L392,101" class="ln warn" fill="none"
          marker-end="url(#ah)"/>
    <text x="484" y="48" class="lb warn">上限超過 → その観点のレベルを下げる</text>
    <text x="664" y="120" class="lb">OK</text>
    {fan}{ob}
  </svg>
  <figcaption>要点は2つ。<b>上限チェックで超過が出たら転記に戻る</b>こと（ここを飛ばすと前提フラグが効きません）、
    そして<b>判定は3方向に分かれ、Cで終わりではない</b>ことです。</figcaption>
</figure>"""


def fig_cap():
    """前提フラグが「加点」ではなく「天井」であることを示す。"""
    f2 = next(f for f in FLAGS if f["id"] == "F2")
    cap = f2["cap"]["C2"]
    CW, GAP, X0, Y, H = 96, 6, 30, 66, 46
    cells = ""
    for i, n in enumerate(range(1, 6)):
        x = X0 + i * (CW + GAP)
        ok = n <= cap
        cells += (
            f'<rect x="{x}" y="{Y}" width="{CW}" height="{H}" rx="8" '
            f'class="{"cl-ok" if ok else "cl-ng"}"/>'
            f'<text x="{x + CW / 2}" y="{Y + 29}" class="{"cl-okt" if ok else "cl-ngt"}">'
            f'レベル{n}</text>')
        if not ok:
            cells += (f'<line x1="{x + 26}" y1="{Y + 13}" x2="{x + CW - 26}" y2="{Y + H - 13}" '
                      f'class="ln bad"/>')
    capx = X0 + cap * (CW + GAP) - GAP / 2
    right = X0 + 5 * (CW + GAP) - GAP
    return f"""
<figure class="dg">
  <svg viewBox="0 0 {right + 30} 152" role="img"
       aria-label="前提フラグF2に該当すると、資料上はレベル5相当でもレベル{cap}が天井になり、それ以上はつけられない。">
    {ARROW}
    <text x="{X0}" y="26" class="lb st">資料の記述だけならレベル5相当</text>
    <path d="M{X0 + 196},20 L{right - 40},20 L{right - 40},{Y - 6}" class="ln" fill="none"
          marker-end="url(#ah)"/>
    {cells}
    <line x1="{capx}" y1="{Y - 14}" x2="{capx}" y2="{Y + H + 14}" class="ln bad dash"/>
    <text x="{capx + 8}" y="{Y + H + 30}" class="lb bad">{f2["id"]} に該当 → ここが天井</text>
    <text x="{X0}" y="{Y + H + 30}" class="lb ok">つけられる</text>
  </svg>
  <figcaption>フラグは加点材料ではありません。該当した瞬間、その観点で到達できるレベルの上が塞がれます
    （図は {E(f2["name"])} が C2 にかける上限）。</figcaption>
</figure>"""


def fig_scale():
    """判定バンドと、全観点を同レベルでつけた場合の位置関係。"""
    X0, X1, Y, H = 44, 844, 56, 36
    px = (X1 - X0) / 100
    def x(v):
        return X0 + v * px
    cuts = [(b[0], b[1]) for b in BANDS][::-1]      # 低い順
    segs = ""
    for i, (lo, lab) in enumerate(cuts):
        hi = cuts[i + 1][0] if i + 1 < len(cuts) else 100
        cls = {"S": "b5", "A": "b2", "B": "b4", "C": "bm"}[lab]
        segs += (f'<rect x="{x(lo):.1f}" y="{Y}" width="{x(hi) - x(lo):.1f}" height="{H}" '
                 f'class="sc {cls}"/>'
                 f'<text x="{(x(lo) + x(hi)) / 2:.1f}" y="{Y + 24}" class="sc-l {cls}">{lab}</text>')
    ticks = "".join(
        f'<text x="{x(v):.1f}" y="{Y + H + 20}" class="tk">{v}</text>'
        for v in sorted({0, 100} | {b[0] for b in BANDS if b[0]}))
    pins = ""
    for n in (3, 4, 5):
        v = flat(n)
        pins += (f'<line x1="{x(v):.1f}" y1="22" x2="{x(v):.1f}" y2="{Y}" class="ln pin"/>'
                 f'<text x="{x(v):.1f}" y="16" class="lb pin" '
                 f'text-anchor="{"end" if v >= 100 else "middle"}">'
                 f'全観点Lv{n} = {int(v)}点</text>')
    return f"""
<figure class="dg">
  <svg viewBox="0 0 888 {Y + H + 30}" role="img"
       aria-label="0点から100点の判定スケール。{'、'.join(f'{b[1]}は{b[0]}点以上' for b in BANDS)}。全観点をレベル3でつけると{int(flat(3))}点、レベル4で{int(flat(4))}点、レベル5で100点。">
    {segs}{ticks}{pins}
  </svg>
  <figcaption>全観点レベル4でちょうど S の下限。
    <b>A（{BANDS[1][0]}〜{BANDS[0][0] - 1}点）はレベル3と4が混在する帯</b>で、全部レベル3では届きません。</figcaption>
</figure>"""


FIG_WEIGHTS = fig_weights()
FIG_FLOW = fig_flow()
FIG_CAP = fig_cap()
FIG_SCALE = fig_scale()

CSS = """
*{box-sizing:border-box}
:root{
  --bg:#FFFFFF; --card:#FFFFFF; --sunk:#F5F7FC;
  --ink:#1E2233; --ink2:#414962; --mute:#6B7189;
  --line:#DCE1EE; --line2:#EBEEF6;
  --pri:#4B4CD6; --pri-s:#EAEAFC; --onc:#FFFFFF;
  --warn:#A15900; --warn-s:#FBEEDC; --bad:#C2372B; --bad-s:#FBEAE8;
  --ok:#07756B; --ok-s:#E1F4F1;
  --h1:#C13A22; --h1s:#FCEAE6;
  --h2:#07756B; --h2s:#E1F4F1;
  --h3:#6244C9; --h3s:#EDE9FB;
  --h4:#A15900; --h4s:#FBEEDC;
  --h5:#B93077; --h5s:#FBE9F2;
  --h6:#155FAF; --h6s:#E4EFFB;
  --sh:0 1px 2px rgba(30,34,51,.06),0 6px 18px -12px rgba(30,34,51,.22);
  --sh2:0 2px 5px rgba(30,34,51,.08),0 14px 30px -16px rgba(30,34,51,.3);
  --r:12px; --r2:8px;
  --disp:"Hiragino Maru Gothic ProN","M PLUS Rounded 1c","Hiragino Sans",
    "Yu Gothic","Noto Sans JP",sans-serif;
  --body:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic","Noto Sans JP","Meiryo",sans-serif;
  --mono:ui-rounded,"SF Mono",ui-monospace,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#12141F; --card:#1B1E2E; --sunk:#161A28;
  --ink:#EDEFF7; --ink2:#C2C8DA; --mute:#9098B0;
  --line:#2C3145; --line2:#232838;
  --pri:#9EA0FF; --pri-s:#242545; --onc:#12141F;
  --warn:#F7B54D; --warn-s:#33280F; --bad:#FF8A7A; --bad-s:#331E1C;
  --ok:#3FD6C2; --ok-s:#12332F;
  --h1:#FF8F79; --h1s:#33211D;
  --h2:#3FD6C2; --h2s:#12332F;
  --h3:#AD97FF; --h3s:#241E3C;
  --h4:#F7B54D; --h4s:#33280F;
  --h5:#FB93C6; --h5s:#331C29;
  --h6:#74B8F5; --h6s:#152738;
  --sh:0 1px 2px rgba(0,0,0,.4),0 8px 22px -14px rgba(0,0,0,.8);
  --sh2:0 2px 6px rgba(0,0,0,.45),0 16px 34px -18px rgba(0,0,0,.9);
}}
:root[data-theme="dark"]{
  --bg:#12141F; --card:#1B1E2E; --sunk:#161A28;
  --ink:#EDEFF7; --ink2:#C2C8DA; --mute:#9098B0;
  --line:#2C3145; --line2:#232838;
  --pri:#9EA0FF; --pri-s:#242545; --onc:#12141F;
  --warn:#F7B54D; --warn-s:#33280F; --bad:#FF8A7A; --bad-s:#331E1C;
  --ok:#3FD6C2; --ok-s:#12332F;
  --h1:#FF8F79; --h1s:#33211D;
  --h2:#3FD6C2; --h2s:#12332F;
  --h3:#AD97FF; --h3s:#241E3C;
  --h4:#F7B54D; --h4s:#33280F;
  --h5:#FB93C6; --h5s:#331C29;
  --h6:#74B8F5; --h6s:#152738;
  --sh:0 1px 2px rgba(0,0,0,.4),0 8px 22px -14px rgba(0,0,0,.8);
  --sh2:0 2px 6px rgba(0,0,0,.45),0 16px 34px -18px rgba(0,0,0,.9);
}
:root[data-theme="light"]{
  --bg:#FFFFFF; --card:#FFFFFF; --sunk:#F5F7FC;
  --ink:#1E2233; --ink2:#414962; --mute:#6B7189;
  --line:#DCE1EE; --line2:#EBEEF6;
  --pri:#4B4CD6; --pri-s:#EAEAFC; --onc:#FFFFFF;
  --warn:#A15900; --warn-s:#FBEEDC; --bad:#C2372B; --bad-s:#FBEAE8;
  --ok:#07756B; --ok-s:#E1F4F1;
  --h1:#C13A22; --h1s:#FCEAE6;
  --h2:#07756B; --h2s:#E1F4F1;
  --h3:#6244C9; --h3s:#EDE9FB;
  --h4:#A15900; --h4s:#FBEEDC;
  --h5:#B93077; --h5s:#FBE9F2;
  --h6:#155FAF; --h6s:#E4EFFB;
  --sh:0 1px 2px rgba(30,34,51,.06),0 6px 18px -12px rgba(30,34,51,.22);
  --sh2:0 2px 5px rgba(30,34,51,.08),0 14px 30px -16px rgba(30,34,51,.3);
}
/* 観点ごとの色。--c＝地色に載る色、--cs＝淡色地 */
.c1{--c:var(--h1);--cs:var(--h1s)} .c2{--c:var(--h2);--cs:var(--h2s)}
.c3{--c:var(--h3);--cs:var(--h3s)} .c4{--c:var(--h4);--cs:var(--h4s)}
.c5{--c:var(--h5);--cs:var(--h5s)} .c6{--c:var(--h6);--cs:var(--h6s)}

body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);
  font-size:14px;line-height:1.8;-webkit-font-smoothing:antialiased;
  font-feature-settings:"palt" 1}
.wrap{max-width:920px;margin:0 auto;padding:0 22px 96px}
section{margin-top:60px}
h2{font-family:var(--disp);font-size:23px;margin:0;font-weight:700;line-height:1.4;
  letter-spacing:.01em;text-wrap:balance}
.sh{display:flex;align-items:center;gap:11px;flex-wrap:wrap;margin-bottom:22px}
.sn{font-family:var(--mono);font-size:12px;font-weight:800;color:var(--onc);
  background:var(--pri);border-radius:999px;padding:3px 12px;flex:none;letter-spacing:.06em}
.ss{margin:0;font-size:12.5px;color:var(--mute);flex:1 1 100%;line-height:1.7}
code{font-family:var(--mono);font-size:.9em;background:var(--pri-s);padding:1px 6px;
  border-radius:5px;color:var(--pri);font-weight:700}

/* hero */
.hero{background:var(--pri);position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;right:-70px;top:-90px;width:290px;height:290px;
  border-radius:50%;background:rgba(255,255,255,.09)}
.hero::before{content:"";position:absolute;right:110px;bottom:-130px;width:190px;height:190px;
  border-radius:50%;background:rgba(255,255,255,.07)}
.hin{max-width:920px;margin:0 auto;padding:38px 22px 32px;position:relative;z-index:1}
.eb{font-family:var(--mono);font-size:10.5px;letter-spacing:.18em;color:rgba(255,255,255,.82);
  margin:0 0 12px;font-weight:800}
.hero h1{font-family:var(--disp);font-size:clamp(26px,3.8vw,34px);margin:0 0 12px;
  color:#fff;font-weight:800;line-height:1.35;text-wrap:balance;letter-spacing:.01em}
.hero h1 em{font-style:normal;font-family:var(--body);font-size:13px;font-weight:700;
  color:#fff;background:rgba(255,255,255,.2);border-radius:999px;padding:3px 12px;
  margin-left:12px;letter-spacing:.04em;white-space:nowrap;vertical-align:middle}
.hero p{margin:0;color:rgba(255,255,255,.9);font-size:13.5px;max-width:62ch;line-height:1.95}
.kpi{display:flex;gap:10px;margin-top:22px;flex-wrap:wrap}
.kpi div{background:rgba(255,255,255,.16);border-radius:var(--r2);padding:8px 16px;
  line-height:1.3;text-align:center}
.kpi b{display:block;font-family:var(--mono);font-size:22px;color:#fff;font-weight:800}
.kpi span{font-size:10px;color:rgba(255,255,255,.85);letter-spacing:.04em}
.ribbon{display:flex;height:7px}
.ribbon i{background:var(--c)}

/* sticky 観点バー */
.bar{position:sticky;top:0;z-index:20;background:var(--card);
  border-bottom:1px solid var(--line);box-shadow:var(--sh)}
.bin{max-width:920px;margin:0 auto;padding:9px 22px;display:flex;gap:6px;
  overflow-x:auto;scrollbar-width:thin}
.sx{flex:1 0 auto;min-width:104px;display:grid;grid-template-columns:auto 1fr auto;
  align-items:center;gap:6px;text-decoration:none;padding:6px 11px;border-radius:999px;
  background:var(--cs);border:1.5px solid transparent;transition:border-color .15s}
.sx:hover{border-color:var(--c)}
.sx b{font-family:var(--mono);font-size:10px;color:var(--c);font-weight:800}
.sx span{font-size:11.5px;color:var(--ink);font-weight:700;white-space:nowrap}
.sx i{font-family:var(--mono);font-style:normal;font-size:13px;font-weight:800;color:var(--c)}

/* テーブル共通 */
table{border-collapse:separate;border-spacing:0;width:100%;background:var(--card);
  font-size:13px;border:1px solid var(--line);border-radius:var(--r);overflow:hidden;
  box-shadow:var(--sh)}
th,td{border-bottom:1px solid var(--line2);padding:9px 13px;text-align:left;
  vertical-align:top}
thead th{background:var(--sunk);font-size:10.5px;letter-spacing:.06em;color:var(--mute);
  font-weight:800;white-space:nowrap}
tbody tr:last-child th,tbody tr:last-child td{border-bottom:none}
tfoot td,tfoot th{border-bottom:none}
.num{font-family:var(--mono);text-align:right;font-variant-numeric:tabular-nums}
.tsc{overflow-x:auto;border-radius:var(--r)}

/* 観点サマリ */
table.sum td.cid{width:44px}
table.sum td.cid a{font-family:var(--mono);font-weight:800;color:var(--onc);
  background:var(--c);text-decoration:none;font-size:11px;padding:3px 8px;
  border-radius:999px;display:inline-block;line-height:1.5}
table.sum th[scope="row"]{font-weight:700;white-space:nowrap}
table.sum .qq{color:var(--mute);font-size:12px;line-height:1.7}
table.sum .wt{font-family:var(--mono);font-weight:800;font-size:19px;text-align:right;
  color:var(--c);white-space:nowrap;font-variant-numeric:tabular-nums}
table.sum tbody tr:hover td,table.sum tbody tr:hover th{background:var(--cs)}
table.sum tfoot td,table.sum tfoot th{background:var(--sunk);font-weight:800}
table.sum tfoot .wt{color:var(--ink)}

/* 手順 */
ol.steps{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:9px}
ol.steps li{display:grid;grid-template-columns:38px 1fr;gap:13px;background:var(--card);
  border:1px solid var(--line);border-radius:var(--r);padding:14px 18px 14px 14px;
  box-shadow:var(--sh)}
.stn{font-family:var(--mono);font-weight:800;font-size:14px;color:var(--onc);
  background:var(--pri);width:28px;height:28px;display:grid;place-items:center;
  border-radius:50%;margin-top:2px}
.stb h3{margin:0 0 3px;font-family:var(--disp);font-size:15px;font-weight:700}
.stb p{margin:0;font-size:12.5px;color:var(--ink2);line-height:1.8}

/* 観点リファレンス */
.ref{background:var(--card);border:1px solid var(--line);border-radius:var(--r);
  margin-bottom:15px;box-shadow:var(--sh);scroll-margin-top:66px;overflow:hidden;
  border-top:4px solid var(--c)}
.ref>header{display:flex;align-items:center;gap:12px;padding:14px 18px 12px;
  background:var(--cs)}
.rid{font-family:var(--mono);font-weight:800;font-size:12px;color:var(--onc);
  background:var(--c);padding:4px 10px;border-radius:999px;flex:none}
.rt{flex:1 1 auto;min-width:0}
.rt h3{margin:0;font-family:var(--disp);font-size:17px;font-weight:700;line-height:1.4}
.rt p{margin:1px 0 0;font-size:12px;color:var(--c);line-height:1.6;font-weight:700}
.rw{font-family:var(--mono);font-size:26px;font-weight:800;color:var(--c);flex:none;
  font-variant-numeric:tabular-nums}
.rw i{font-style:normal;font-size:11px;color:var(--mute);margin-left:1px}
.rwho{display:flex;flex-wrap:wrap;align-items:center;gap:5px;padding:9px 18px;
  background:var(--card);border-bottom:1px solid var(--line2)}
.wl{font-size:10px;letter-spacing:.1em;color:var(--mute);font-weight:800;margin-right:3px}
.jt{font-size:11.5px;text-decoration:none;padding:2px 10px;border-radius:999px;
  white-space:nowrap;border:1.5px solid transparent}
.jd{background:var(--cs);color:var(--c);font-weight:800}
.jo{color:var(--mute);background:var(--sunk)}
.jt:hover{border-color:var(--c)}
table.lvt{border:none;box-shadow:none;border-radius:0}
table.lvt thead th{background:transparent;padding:8px 14px 6px}
table.lvt thead th:last-child{text-align:right}
table.lvt td{padding:10px 14px}
td.lv{width:40px;text-align:center;padding-left:14px}
td.lv span{font-family:var(--mono);font-weight:800;font-size:12px;width:24px;height:24px;
  display:inline-grid;place-items:center;border-radius:50%;color:var(--mute);
  background:var(--sunk)}
tr.top td.lv span{background:var(--c);color:var(--onc)}
tr.top{background:var(--cs)}
td.lvd{font-size:12.5px;line-height:1.75;color:var(--ink2)}
tr.top td.lvd{color:var(--ink);font-weight:500}
td.lvp{font-family:var(--mono);width:56px;text-align:right;color:var(--c);font-weight:800;
  font-variant-numeric:tabular-nums;font-size:14px}
.capbox{background:var(--warn-s);padding:10px 16px}
.capbox h5{margin:0 0 4px;font-size:10.5px;letter-spacing:.08em;color:var(--warn);
  font-weight:800}
.capbox ul{margin:0;padding-left:17px;font-size:12px;line-height:1.85;color:var(--ink2)}
.capbox b{font-family:var(--mono);color:var(--warn)}
.capbox em{font-style:normal;font-weight:800;color:var(--warn)}

/* 審査員別 重視観点マトリクス */
table.mx{min-width:700px}
table.mx thead th{background:var(--sunk);border-bottom:none;padding:0;text-align:center;
  vertical-align:bottom}
table.mx thead th:first-child{text-align:left;padding:10px 13px;vertical-align:bottom}
table.mx thead th a{text-decoration:none;display:block;background:var(--c);padding:8px 6px}
table.mx thead th a b{display:block;font-family:var(--mono);font-size:9.5px;
  color:var(--onc);opacity:.8;letter-spacing:.06em;font-weight:800}
table.mx thead th a span{display:block;font-size:11.5px;color:var(--onc);font-weight:800;
  line-height:1.35;margin:1px 0;white-space:nowrap}
table.mx thead th a i{display:block;font-style:normal;font-family:var(--mono);
  font-size:9.5px;color:var(--onc);opacity:.8;font-weight:700}
table.mx tbody th{white-space:nowrap;padding:9px 13px;vertical-align:middle}
table.mx tbody th b{display:block;font-size:13px;font-weight:700}
table.mx tbody th i{display:block;font-style:normal;font-size:10px;color:var(--mute);
  line-height:1.45}
table.mx td{text-align:center;vertical-align:middle;padding:8px 4px}
table.mx td span{display:inline-grid;place-items:center;width:26px;height:26px;
  border-radius:50%;font-size:13px;font-weight:800;line-height:1}
table.mx td.d span{background:var(--c);color:var(--onc)}
table.mx td.o span{color:var(--c);background:var(--cs)}
table.mx tbody tr:hover td,table.mx tbody tr:hover th{background:var(--sunk)}
table.mx tfoot td,table.mx tfoot th{background:var(--sunk);padding:8px 4px;text-align:center}
table.mx tfoot th{text-align:right;padding-right:12px;font-size:10.5px;color:var(--mute);
  letter-spacing:.06em;white-space:nowrap;font-weight:800}
table.mx tfoot td b{font-family:var(--mono);font-size:16px;color:var(--c);font-weight:800}
table.mx tfoot td span{font-size:9.5px;color:var(--mute);margin-left:1px}
.mxlg{display:flex;gap:16px;flex-wrap:wrap;margin-top:12px;font-size:11.5px;
  color:var(--mute);align-items:center}
.mxlg i{font-style:normal;display:inline-grid;place-items:center;width:22px;height:22px;
  border-radius:50%;font-size:12px;font-weight:800;margin-right:5px;vertical-align:middle}
.lgd{background:var(--pri);color:var(--onc)}
.lgo{background:var(--pri-s);color:var(--pri)}

/* 本人の言葉 */
.qgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(268px,1fr));gap:13px;
  margin-top:18px}
.qt{background:var(--card);border:1px solid var(--line);border-radius:var(--r);
  padding:14px 16px;box-shadow:var(--sh);display:flex;flex-direction:column;gap:9px}
.qh h3{margin:0;font-family:var(--disp);font-size:15px;font-weight:700}
.qh p{margin:0;font-size:10px;color:var(--mute);line-height:1.5}
.qt blockquote{margin:0;padding-left:12px;border-left:3px solid var(--pri-s);flex:1;
  font-size:11.5px;line-height:1.85;color:var(--ink2)}
.qc{display:flex;flex-wrap:wrap;gap:5px}
.qchip{font-family:var(--mono);font-size:10px;text-decoration:none;padding:3px 9px;
  border-radius:999px;background:var(--cs);color:var(--c);font-weight:800;
  letter-spacing:.02em}

/* フラグ */
.fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:13px}
.fg{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--warn);
  border-radius:var(--r);padding:14px 17px;box-shadow:var(--sh)}
.fgh{display:flex;align-items:center;gap:9px;margin-bottom:7px}
.fgid{font-family:var(--mono);font-weight:800;font-size:11px;color:var(--onc);
  background:var(--warn);padding:3px 10px;border-radius:999px}
.fg h3{margin:0;font-family:var(--disp);font-size:14.5px;font-weight:700}
.fgd{margin:0 0 9px;font-size:12.5px;color:var(--ink2);line-height:1.75}
.fgc{margin:0;font-size:12px;color:var(--warn);font-weight:800;line-height:1.7;
  background:var(--warn-s);border-radius:var(--r2);padding:7px 11px}
.fgc b{font-family:var(--mono)}

/* 判定 */
.bl{width:56px;text-align:center;vertical-align:middle}
.bl span{font-family:var(--mono);font-weight:800;font-size:15px;width:30px;height:30px;
  display:inline-grid;place-items:center;border-radius:50%;color:var(--onc)}
.b-S span{background:var(--h5)} .b-A span{background:var(--h2)}
.b-B span{background:var(--h4)} .b-C span{background:var(--mute)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}
.two>div{min-width:0}
h4{font-family:var(--disp);font-size:13px;color:var(--ink);margin:0 0 10px;font-weight:700}
table.qk th,table.qk td{padding:9px 10px}
table.qk th[scope="row"]{white-space:nowrap;font-weight:700;font-size:12.5px}
table.qk th[scope="row"] span{display:block;font-family:var(--mono);font-size:10px;
  color:var(--mute);font-weight:400;letter-spacing:.04em}
table.qk td{font-size:14px;font-weight:800;color:var(--pri)}
table.cb .big{font-size:18px;font-weight:800;color:var(--pri)}
ol.tie{margin:10px 0 0;padding-left:20px;font-size:12.5px;color:var(--ink2);line-height:2}
ol.tie li::marker{color:var(--pri);font-family:var(--mono);font-weight:800}

/* やってはいけない */
ul.dont{list-style:none;margin:0;padding:0;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(268px,1fr));gap:13px}
ul.dont li{background:var(--card);border:1px solid var(--line);border-radius:var(--r);
  padding:14px 16px 14px 44px;box-shadow:var(--sh);position:relative}
ul.dont li::before{position:absolute;left:14px;top:14px;font-family:var(--mono);
  font-weight:800;font-size:12px;width:22px;height:22px;display:grid;place-items:center;
  border-radius:50%}
ul.dont li.no::before{content:"×";background:var(--bad-s);color:var(--bad)}
ul.dont li.warn::before{content:"!";background:var(--pri-s);color:var(--pri)}
ul.dont h3{margin:0 0 4px;font-family:var(--disp);font-size:13.5px;font-weight:700;
  line-height:1.5}
ul.dont p{margin:0;font-size:12px;color:var(--ink2);line-height:1.75}

/* 図解 */
.dg{margin:0 0 20px;padding:16px 18px 12px;background:var(--card);border:1px solid var(--line);
  border-radius:var(--r);box-shadow:var(--sh);color:var(--ink)}
.dg svg{display:block;width:100%;max-width:100%;height:auto;overflow:visible}
.dg figcaption{margin-top:12px;font-size:11.5px;color:var(--mute);line-height:1.75;
  border-top:1px solid var(--line2);padding-top:9px}
.dg figcaption b{color:var(--ink2)}
.dg text{font-family:var(--body);fill:currentColor}
.sg-id{font-family:var(--mono);font-size:12px;font-weight:800;text-anchor:middle;fill:var(--onc)}
.sg-w{font-size:15px;font-weight:800;text-anchor:middle;fill:var(--onc)}
.sg-n{font-size:11px;text-anchor:middle;fill:var(--mute)}
.dg .ln{stroke:currentColor;stroke-width:1.6;opacity:.55;fill:none}
.dg .ln.warn{stroke:var(--warn);opacity:1;stroke-width:1.8}
.dg .ln.bad{stroke:var(--bad);opacity:1;stroke-width:2}
.dg .ln.dash{stroke-dasharray:5 4}
.dg .ln.pin{stroke:var(--pri);opacity:.55;stroke-dasharray:3 3}
.dg .bx{fill:var(--card);stroke:currentColor;stroke-width:1.4;opacity:1;
  stroke-opacity:.28}
.dg .bt{font-size:13px;font-weight:700;text-anchor:middle}
.dg .bs{font-size:10.5px;text-anchor:middle;fill:var(--mute)}
.dg .lb{font-size:11px;text-anchor:middle}
.dg .lb.st{text-anchor:start}
.dg .lb.warn{fill:var(--warn);font-weight:700}
.dg .lb.bad{fill:var(--bad);font-weight:700;text-anchor:start}
.dg .lb.ok{fill:var(--ok);font-weight:700;text-anchor:start}
.dg .lb.pin{fill:var(--pri);font-weight:700;font-size:10.5px}
.dg .dia{fill:var(--warn-s);stroke:var(--warn);stroke-width:1.8}
.dg .dia-t{fill:var(--warn)}
.dg .bl2{font-family:var(--mono);font-size:13px;font-weight:800;text-anchor:start}
.dg .bs2{font-size:11px;text-anchor:start;fill:var(--ink2)}
.dg .b5{fill:var(--h5s);stroke:var(--h5)} .dg text.b5,.dg .sc-l.b5{fill:var(--h5);stroke:none}
.dg .b2{fill:var(--h2s);stroke:var(--h2)} .dg text.b2,.dg .sc-l.b2{fill:var(--h2);stroke:none}
.dg .b4{fill:var(--h4s);stroke:var(--h4)} .dg text.b4,.dg .sc-l.b4{fill:var(--h4);stroke:none}
.dg .bm{fill:var(--sunk);stroke:var(--mute)} .dg text.bm,.dg .sc-l.bm{fill:var(--mute);stroke:none}
.dg .cl-ok{fill:var(--ok-s);stroke:var(--ok);stroke-width:1.6}
.dg .cl-okt{font-size:12px;font-weight:700;text-anchor:middle;fill:var(--ok)}
.dg .cl-ng{fill:var(--sunk);stroke:currentColor;stroke-width:1.2;stroke-opacity:.25}
.dg .cl-ngt{font-size:12px;text-anchor:middle;fill:var(--mute)}
.dg .sc{stroke-width:0}
.dg .sc-l{font-size:15px;font-weight:800;text-anchor:middle;font-family:var(--mono)}
.dg .tk{font-size:10.5px;text-anchor:middle;fill:var(--mute);font-family:var(--mono)}

.note{background:var(--pri-s);border-radius:var(--r);padding:14px 18px;font-size:12.5px;
  color:var(--ink2);line-height:1.85;margin-top:18px}
.note b{color:var(--ink)}
footer{margin-top:60px;padding-top:18px;border-top:1px solid var(--line);
  font-size:11px;color:var(--mute);line-height:1.85}
a{color:var(--pri)}
a:focus-visible{outline:2px solid var(--pri);outline-offset:2px}
@media (max-width:720px){
  .two{grid-template-columns:1fr}
  .bar{position:static}
  .ref>header{flex-wrap:wrap}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media print{
  .bar{display:none}
  body{background:#fff;font-size:10.5pt}
  .ref,.fg,ol.steps li,ul.dont li,table,.qt{box-shadow:none;break-inside:avoid}
  section{margin-top:24px}
  .hero,.ribbon{-webkit-print-color-adjust:exact;print-color-adjust:exact}
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
<div class="ribbon">{ribbon}</div>

<nav class="bar"><div class="bin">{sticky}</div></nav>

<div class="wrap">

<section>
  <div class="sh"><span class="sn">01</span><h2>採点する6つの観点</h2>
    <p class="ss">配点は{STEP}点刻み・合計{TOTAL}点。各観点をレベル1〜5でつけ、レベル ÷ 5 × 配点 が得点になります。
    観点ごとの色は、この資料のどこでも同じものを使っています。</p></div>
  {FIG_WEIGHTS}
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

<section id="jm">
  <div class="sh"><span class="sn">02</span><h2>どの役員がどの観点を重視しているか</h2>
    <p class="ss">◎＝グランドフィナーレコメントで直接この観点を挙げている（＝重視）。○＝各ステージ向けの審査コメントから補助的に反映。</p></div>
  <div class="tsc"><table class="mx">
    <thead><tr><th>審査員</th>{mxhead}</tr></thead>
    <tbody>{"".join(mxrows)}</tbody>
    <tfoot><tr><th>◎ の審査員数</th>{mxfoot}</tr></tfoot>
  </table></div>
  <div class="mxlg">
    <span><i class="lgd">◎</i>この観点を直接挙げている（重視）</span>
    <span><i class="lgo">○</i>審査コメントから補助的に反映</span>
    <span>観点名はクリックで移動します</span>
  </div>
  <div class="note">
    <b>配点はこの表から決まっています。</b>
    ◎を1.0、○を0.5として観点ごとに数え、100点に正規化したうえで{STEP}点刻みに丸めました。
    「多くの役員が挙げた観点ほど配点が重い」という関係になっており、役職による重み付けは入れていません。
    採点結果を報告する際は、この表を使って「どの役員の観点でどう評価されたか」を説明できます。
  </div>

  <h4 style="margin-top:28px">グランドフィナーレに向けた本人の言葉</h4>
  <div class="qgrid">{quotes}</div>
</section>

<section>
  <div class="sh"><span class="sn">03</span><h2>採点の手順</h2>
    <p class="ss">1件あたりの流れ。ステップ4を飛ばすと前提フラグが効かないまま順位が出ます。</p></div>
  {FIG_FLOW}
  <ol class="steps">{steps}</ol>
</section>

<section>
  <div class="sh"><span class="sn">04</span><h2>観点別 採点リファレンス</h2>
    <p class="ss">レベルは上から5〜1。右端はその観点で入る得点です。迷ったら低いほうをつけてください。</p></div>
  {"".join(refs)}
</section>

<section>
  <div class="sh"><span class="sn">05</span><h2>前提フラグ</h2>
    <p class="ss">加点ではなく上限です。該当したら、その観点は指定レベル以上をつけられません。</p></div>
  {FIG_CAP}
  <div class="fgrid">{flagcards}</div>
  <div class="note">
    <b>なぜ加点ではなく上限なのか。</b>
    「生産性向上は企業として取り組むべき前提」「何をAIで実現したかよりも文化」というのが審査員の言葉でした。
    これらを加点材料にすると、数値の大きい応募がそのまま上位に来てしまいます。
    採点シートの <code>W列 上限チェック</code> が、フラグと入力レベルの矛盾を自動で検出します。
  </div>
</section>

<section>
  <div class="sh"><span class="sn">06</span><h2>判定と得点の目安</h2>
    <p class="ss">総合点から判定が自動で決まります。同点時は下記の順で比較します。</p></div>
  {FIG_SCALE}
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
    <b>{next(c['id'] for c in CRITERIA if c['weight']==max(WEIGHTS))}
    （{next(c['short'] for c in CRITERIA if c['weight']==max(WEIGHTS))}）が単独で最も重い{max(WEIGHTS)}点です。</b>
    同点はまずここのレベル差で見るのが最も情報量が大きく、次点で並ぶ
    {"・".join(c["id"] for c in CRITERIA if c["weight"] == sorted(set(WEIGHTS))[-2])}
    （{sorted(set(WEIGHTS))[-2]}点）で見てください。それでも並ぶ場合は事務局・役員の合議で決めます。
  </div>
</section>

<section>
  <div class="sh"><span class="sn">07</span><h2>採点で気をつけること</h2>
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
