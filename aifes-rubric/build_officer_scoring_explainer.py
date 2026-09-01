# -*- coding: utf-8 -*-
"""
役員予備審査「採点のしくみ」説明HTMLを生成する。

役員予備審査ツール（build_officer_prelim_tool.py）が実装している集計ロジック
―特に同点になったときの優先順位（タイブレーク）―を、役員・事務局向けに
文章と図で説明するための1枚もの。ロジックの定義元は officer_prelim_data.py
（POINTS_BY_RANK / TIEBREAK_OFFICER）であり、この説明書はそこから生成するので、
ルールを変えたら officer_prelim_data.py を直せば両方に反映される。
配色は役員予備審査ツール本体（build_officer_prelim_tool.py の CSS）に合わせた
ネイビー×ゴールド。
"""
import html

from rubric_data import CRITERIA, WEIGHTS, BANDS
from officer_prelim_data import OFFICERS, GF_ENTRIES, POINTS_BY_RANK, TIEBREAK_OFFICER


def E(s):
    return html.escape(str(s), quote=True)


CSS = """
:root{
  --navy:#143058; --navy-deep:#0d2140; --navy-soft:#2a4a76;
  --gold:#FFCD00; --gold-dim:#c9a300;
  --paper:#f4f6f9; --card:#ffffff; --ink:#1a2233; --mute:#6b7789; --line:#dde3ec;
  --ok:#1f9d6b; --ok-s:#eafaf1;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Yu Gothic UI","Meiryo","Segoe UI",-apple-system,sans-serif;background:var(--paper);color:var(--ink);font-size:14px;line-height:1.8}
.wrap{max-width:920px;margin:0 auto;padding:0 0 60px}
header{background:linear-gradient(120deg,var(--navy),var(--navy-soft));color:#fff;padding:40px 36px;border-bottom:4px solid var(--gold)}
header .en{font-size:11px;letter-spacing:.18em;color:var(--gold);font-weight:700}
header h1{font-size:26px;margin:8px 0 10px;font-weight:700}
header p{font-size:13.5px;color:#cadcfc;max-width:640px}
main{padding:36px}
.flow{display:flex;align-items:stretch;gap:0;flex-wrap:wrap;margin-bottom:8px}
.flow-step{flex:1;min-width:130px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 12px;text-align:center}
.flow-step b{display:block;font-size:13px;color:var(--navy)}
.flow-step span{display:block;font-size:11px;color:var(--mute);margin-top:4px}
.flow-arw{flex:none;display:flex;align-items:center;justify-content:center;width:28px;color:var(--gold-dim);font-size:16px;font-weight:700}
.flow-step.hl{background:var(--navy);border-color:var(--navy)}
.flow-step.hl b{color:#fff}
.flow-step.hl span{color:#cadcfc}
.sec{margin:36px 0}
.sec-tag{font-size:11px;letter-spacing:.14em;color:var(--gold-dim);font-weight:700;margin-bottom:6px}
.sec h2{font-size:19px;color:var(--navy-deep);margin-bottom:12px;padding-bottom:10px;border-bottom:2px solid var(--gold)}
.sec p.lead{font-size:13.5px;color:var(--mute);margin-bottom:16px}
table.plain{width:100%;border-collapse:collapse;font-size:13px;margin:14px 0}
table.plain th,table.plain td{border-bottom:1px solid var(--line);padding:9px 8px;text-align:left}
table.plain th{color:var(--mute);font-weight:700;font-size:11px}
table.plain td.num{text-align:center;font-weight:700;color:var(--navy)}
.pointrow{display:flex;gap:10px;margin:18px 0;flex-wrap:wrap}
.ptbox{flex:1;min-width:90px;text-align:center;border-radius:10px;padding:16px 8px;border:2px solid var(--line);background:var(--card)}
.ptbox.top{border-color:var(--gold);background:#fffbea}
.ptbox .r{font-size:12px;color:var(--mute);font-weight:700}
.ptbox .p{font-size:26px;font-weight:800;color:var(--navy);margin-top:4px}
.protect{background:var(--card);border:1.5px solid var(--gold);border-radius:10px;padding:18px 20px;margin:16px 0}
.protect .tag{display:inline-block;background:var(--gold);color:var(--navy-deep);font-size:11px;font-weight:800;padding:3px 10px;border-radius:99px;margin-bottom:8px}
.example{background:#f6f8fb;border:1px dashed #c9d4e2;border-radius:10px;padding:16px 20px;margin:14px 0;font-size:12.5px;color:#334}
.tb-list{list-style:none;counter-reset:tb}
.tb-list li{counter-increment:tb;position:relative;padding:12px 0 12px 46px;border-bottom:1px solid var(--line)}
.tb-list li:last-child{border-bottom:0}
.tb-list li::before{content:counter(tb);position:absolute;left:0;top:10px;width:30px;height:30px;border-radius:50%;background:var(--navy);color:#fff;font-weight:800;font-size:13px;display:flex;align-items:center;justify-content:center}
.tb-list li.final::before{background:var(--gold-dim);color:#fff}
.tb-list li b{display:block;font-size:14px;color:var(--ink)}
.worked{margin-top:16px}
.worked table.plain td.win{color:var(--ok);font-weight:800}
.worked .verdict{margin-top:10px;background:var(--ok-s);color:#0d6b46;border-radius:8px;padding:10px 14px;font-size:12.5px}
.foot{font-size:11.5px;color:var(--mute);border-top:1px solid var(--line);padding-top:16px;margin-top:36px}
.band-tbl td.S{color:#1f7a4d;font-weight:800}
.band-tbl td.A{color:#155faf;font-weight:800}
.band-tbl td.B{color:#a15900;font-weight:800}
.band-tbl td.C{color:#c2372b;font-weight:800}
"""


def flow():
    steps = [
        ("応募", f"{len(GF_ENTRIES)}部門"),
        ("AI予備審査", "6観点・100点満点"),
        ("役員予備審査", f"{len(OFFICERS)}名・1〜4位を投票", True),
        ("集計", "点数化＋タイブレーク", True),
        ("決勝進出4部門", "9/15 本戦（12名）へ"),
    ]
    out = []
    for i, s in enumerate(steps):
        title, sub = s[0], s[1]
        hl = len(s) > 2 and s[2]
        if i:
            out.append('<div class="flow-arw">→</div>')
        out.append(f'<div class="flow-step{" hl" if hl else ""}"><b>{E(title)}</b><span>{E(sub)}</span></div>')
    return '<div class="flow">' + "".join(out) + "</div>"


def ai_recap():
    rows = "".join(
        f"<tr><td>{E(c['short'])}</td><td class='num'>{w}点</td></tr>"
        for c, w in zip(CRITERIA, WEIGHTS)
    )
    band_rows = "".join(
        f"<tr><td class='{label}'>{label}</td><td>{lo}点以上</td><td>{E(desc)}</td></tr>"
        for lo, label, desc in BANDS
    )
    return f"""
    <div class="sec">
      <div class="sec-tag">STEP 1</div>
      <h2>AI予備審査（6観点・100点満点）</h2>
      <p class="lead">全応募をAIが6観点で読み、根拠つきでレベル1〜5をつける。配点は審査員コメントの言及数から機械的に算出しており、恣意的な重みづけはしていない。</p>
      <table class="plain">
        <thead><tr><th>観点</th><th>配点</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <table class="plain band-tbl">
        <thead><tr><th>判定</th><th>目安</th><th>意味</th></tr></thead>
        <tbody>{band_rows}</tbody>
      </table>
      <p class="lead" style="margin-top:10px">この点数はあくまで<b>役員が読む前の参考値</b>。決勝進出の可否を機械的に決めるものではない。</p>
    </div>"""


def points_section():
    boxes = "".join(
        f'<div class="ptbox{" top" if rank == 1 else ""}"><div class="r">{rank}位</div><div class="p">{pt}<small style="font-size:12px;color:var(--mute)"> 点</small></div></div>'
        for rank, pt in sorted(POINTS_BY_RANK.items())
    )
    max_total = max(POINTS_BY_RANK.values()) * len(OFFICERS)
    return f"""
    <div class="sec">
      <div class="sec-tag">STEP 2</div>
      <h2>役員予備審査：投票を点数に変換する</h2>
      <p class="lead">{len(OFFICERS)}名の役員が、AI予備審査の結果を参考にしたうえで、決勝に進めたい順に1〜4位を選ぶ。選ばれなかった部門は0点。</p>
      <div class="pointrow">{boxes}</div>
      <p class="lead">{len(OFFICERS)}名分を部門ごとに合算する（最大 {max_total}点）。この合計点が「② 集計結果」の合計点列になる。</p>
    </div>"""


def advance_section():
    return f"""
    <div class="sec">
      <div class="sec-tag">STEP 3</div>
      <h2>決勝進出4部門の決め方</h2>
      <div class="protect">
        <span class="tag">決勝進出</span>
        <p><b>合計点が高い順に上位4部門</b>が決勝進出となる。1位に選んだ役員がいるというだけで、
           合計点にかかわらず無条件に決勝進出することはない。</p>
      </div>
      <div class="example">
        <b>「1位あり」表示について：</b>
        集計結果には、誰か1人でも1位に選んだ部門かどうかを参考情報として表示する。
        これは決勝進出を決めるものではなく、<b>合計点が並んだときのタイブレーク（次のSTEP）</b>の
        材料として使う。
      </div>
    </div>"""


def tiebreak_section():
    items = "".join(
        f'<li class="{"final" if i == len(TIEBREAK_OFFICER) - 1 else ""}"><b>{E(t)}</b></li>'
        for i, t in enumerate(TIEBREAK_OFFICER)
    )
    return f"""
    <div class="sec">
      <div class="sec-tag">STEP 4</div>
      <h2>同点になったときの優先順位</h2>
      <p class="lead">合計点が並んだ場合、以下の順で機械的に上位を決める。人の判断が入るのは、それでも並んだ最後の1点だけ。</p>
      <ol class="tb-list">{items}</ol>
    </div>"""


def worked_example():
    a = next(e for e in GF_ENTRIES if e["dept"] == "CMS本部 MSC")
    b = next(e for e in GF_ENTRIES if e["dept"] == "HR戦略本部 人材開発部")
    return f"""
    <div class="sec worked">
      <div class="sec-tag">想定例</div>
      <h2>タイブレークの動き方（仮のケース）</h2>
      <p class="lead">実際の投票結果ではなく、動き方を示すための仮の例。4名の投票結果、2部門がまったく同じ得票（1位1票・2位1票・3位1票・4位1票＝31点）になったと仮定する。</p>
      <table class="plain">
        <thead><tr><th>部門</th><th>1位</th><th>2位</th><th>3位</th><th>4位</th><th>合計点</th><th>AI予備審査</th><th>結果</th></tr></thead>
        <tbody>
          <tr>
            <td>{E(a['dept'])}</td><td class="num">1</td><td class="num">1</td><td class="num">1</td><td class="num">1</td>
            <td class="num">31</td><td class="num">{a['avg']}点</td><td class="win">上位</td>
          </tr>
          <tr>
            <td>{E(b['dept'])}</td><td class="num">1</td><td class="num">1</td><td class="num">1</td><td class="num">1</td>
            <td class="num">31</td><td class="num">{b['avg']}点</td><td>下位</td>
          </tr>
        </tbody>
      </table>
      <div class="verdict">
        合計点・1位票数・2位票数がすべて同じため、④のAI予備審査点まで進み、{a['avg']}点の{E(a['dept'])}が上位と判定される。
      </div>
    </div>"""


HTML = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AIFES 2026 グランドフィナーレ 役員予備審査 採点のしくみ</title>
<style>{CSS}</style></head>
<body>
<div class="wrap">
<header>
  <div class="en">AIFES 2026 GRAND FINALE</div>
  <h1>役員予備審査、採点のしくみ</h1>
  <p>AI予備審査から決勝進出4部門が決まるまでの流れと、同点になったときの優先順位（タイブレーク）を1枚にまとめたもの。役員予備審査ツール（HTML）の集計ロジックと完全に一致する。</p>
</header>
<main>
  {flow()}
  {ai_recap()}
  {points_section()}
  {advance_section()}
  {tiebreak_section()}
  {worked_example()}
  <div class="foot">
    このしくみは役員予備審査ツール（HTML版）専用のロジック。Excel「04_役員予備審査投票」シートは別実装（完全に独立したツールとして運用、2026-08-27合意）。
    9/15本戦・12名審査員による最終順位の同点処理はこれとは別に定める（総合得点→傾斜配分→満点をつけた審査員の数→社長選定、堤さん案）。
  </div>
</main>
</div>
</body></html>"""

if __name__ == "__main__":
    import pathlib
    out = pathlib.Path(__file__).parent / "役員予備審査_採点のしくみ.html"
    out.write_text(HTML, encoding="utf-8")
    print(out.name, len(HTML), "chars")
