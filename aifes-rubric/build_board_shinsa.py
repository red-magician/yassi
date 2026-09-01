# -*- coding: utf-8 -*-
"""上司へ返す論点整理ボード（決まったこと／まだ空いていること）。

decision-board-design スキルの assets/board.css と部品をそのまま使う。
確定事項はチェックリスト（.chk）、未決の論点は疑問形の論点カード（.card）で
視覚的に分ける。混ぜるとどこを議論すべきか分からなくなるため。
"""
import pathlib

# 同期先のパスにセッションIDが挟まることがあるため、都度グロブで探す。
_candidates = sorted(pathlib.Path("/root/.claude/skills/synced").glob("**/decision-board-design/assets/board.css"))
if not _candidates:
    raise FileNotFoundError("decision-board-design スキルの board.css が見つかりません。スキルを再同期してください。")
CSS = _candidates[0].read_text(encoding="utf-8")

ICO = dict(
    doc='<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z"/><path d="M14 3v5h5M8 13h8M8 17h5"/>',
    ai='<rect x="6" y="7" width="12" height="11" rx="2.5"/><path d="M12 4v3M9.5 12h.01M14.5 12h.01M9.5 15.5h5"/><path d="M3 11v3M21 11v3"/>',
    people='<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M16 6.5a3 3 0 0 1 0 5.8M17 20a6 6 0 0 0-2-4.4"/>',
    mic='<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6"/>',
    q='<circle cx="12" cy="12" r="9"/><path d="M9.3 9.2a2.8 2.8 0 0 1 5.4 1c0 1.9-2.7 2.3-2.7 4"/><circle cx="12" cy="17.2" r=".9" fill="currentColor" stroke="none"/>',
    cal='<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    bulb='<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.3.3.5.7.5 1.1h6c0-.4.2-.8.5-1.1A6 6 0 0 0 12 3z"/>',
    cup='<path d="M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3"/><path d="M12 14v3M9 20h6"/>',
)


def ico(name, cls="ico", color=None):
    st = f' style="color:{color}"' if color else ""
    return (f'<svg class="{cls}"{st} viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true">{ICO[name]}</svg>')


def chk(items):
    return '<ul class="chk">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def cards(items, n_cls, cols):
    out = []
    for i, (title, opts) in enumerate(items, 1):
        li = "".join(f"<li>{o}</li>" for o in opts)
        out.append(f'<div class="card"><div class="card-h"><span class="n {n_cls}">{i}</span>'
                   f'<h4>{title}</h4></div><ul>{li}</ul></div>')
    return f'<div class="cards c{cols}">{"".join(out)}</div>'


# ── タイムライン ───────────────────────────────────────────────
TL = [
    ("8/31", "応募締切", False),
    ("9月初旬", "AI予備審査：全応募を6観点で整理", False),
    ("9/4ごろ", "役員4名へ資料配布（五十音順）", False),
    ("9/10", "役員予備審査：順位投票 → 決勝4部決定", True),
    ("9/15 当日", "12名がスタジオで最終審査 → 表彰", False),
]
tl = '<span class="tl-arw">▶</span>'.join(
    f'<div class="tl-step{" on" if on else ""}"><b>{d}</b><span>{t}</span></div>'
    for d, t, on in TL)

# ── C：まだ決まっていない運用の論点 ─────────────────────────────
C = [
    ("登壇順はどう決める？", ["抽選にする？", "予選順位を使う？", "事務局が演出で決める？"]),
    ("入力ツールは何を使う？", ["スマホ／PCどちらで入力？", "集計・表示は自動化する？", "トラブル時の代替手段は？"]),
    ("記録と説明責任は？", ["予選の投票記録をどこまで残す？", "落選部門にどう説明する？", "社内にはいつ何を出す？"]),
    ("講評は誰が書く？", ["6観点をそのまま使う？", "全部門に返す？ 決勝4部だけ？", "AIの根拠抽出を流用する？"]),
    ("発表と表彰の段取りは？", ["順位はいつ確定して誰が発表する？", "点数は公開する？ 非公開？", "表彰の流れ・時間配分は？"]),
]

# ── 予選の配点表（SVG。面積ではなく数値の対比を見せる） ───────────
def fig_points():
    rows = [(1, 10), (2, 8), (3, 7), (4, 6), ("5位以下", 0)]
    x0, w, gap, y, h = 4, 116, 8, 24, 40
    cells = ""
    for i, (rank, pt) in enumerate(rows):
        x = x0 + i * (w + gap)
        top = (i == 0)
        cells += (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" '
            f'class="{"pt-top" if top else ("pt-out" if pt == 0 else "pt-in")}"/>'
            f'<text x="{x + w / 2}" y="{y + 17}" class="pt-r">'
            f'{rank if isinstance(rank, str) else str(rank) + "位"}</text>'
            f'<text x="{x + w / 2}" y="{y + 34}" class="pt-p">{pt}点</text>')
    return f"""
<svg class="dgm" viewBox="0 0 {x0 * 2 + 5 * w + 4 * gap} 76" role="img"
     aria-label="役員1名がつける順位点。1位10点、2位8点、3位7点、4位6点、5位以下は0点。">
  {cells}
  <text x="{x0}" y="14" class="pt-cap">役員1名がつける点（4名分を合計）</text>
  <text x="{x0 + 5 * w + 4 * gap}" y="14" class="pt-cap" text-anchor="end">合計40点満点</text>
</svg>"""


HTML = f"""<title>グランドフィナーレの審査、この設計で決め切れるか？ ― 決まったこと／残る論点 ―</title>
<style>{CSS}
.dgm .pt-top{{fill:var(--gold-s);stroke:var(--gold);stroke-width:2}}
.dgm .pt-in{{fill:var(--grn-s);stroke:var(--grn);stroke-width:1.4}}
.dgm .pt-out{{fill:var(--gry-s);stroke:var(--line);stroke-width:1.4}}
.dgm .pt-r{{font-size:12px;text-anchor:middle;fill:var(--gry)}}
.dgm .pt-p{{font-size:16px;font-weight:800;text-anchor:middle;fill:var(--ink)}}
.dgm .pt-cap{{font-size:11px;fill:var(--gry)}}
</style>
<div class="scroll"><div class="stage"><div class="board">

<div class="hd">
  <h1>グランドフィナーレの審査、この設計で決め切れるか<q>？</q>
      <em>― 決まったこと／残る論点 ―</em></h1>
  <p class="sub">上司資料の26論点のうち<b>18が確定</b>しました。残るのは運用系の5項目です。
     応募は13件、予備審査は役員4名、最終審査は12名という前提で組み直しています。</p>
</div>

<div class="two-a">
  <div class="pre">
    <div class="pre-lab">前提</div>
    <div class="pre-body">
      <div class="flow" style="flex:1">
        <div class="flow-step">{ico('doc')}<b>応募資料</b><span>13件</span></div>
        <span class="flow-arw">→</span>
        <div class="flow-step">{ico('ai')}<b>AI予備審査</b><span>6観点で整理・根拠抽出</span></div>
        <span class="flow-arw">→</span>
        <div class="flow-step">{ico('people')}<b>役員予備審査</b><span>4名・順位投票</span></div>
        <span class="flow-arw">→</span>
        <div class="flow-step">{ico('mic')}<b>本番審査</b><span>12名・スタジオ</span></div>
      </div>
    </div>
  </div>

  <div class="hi hi-red">
    <h3>重要な考え方</h3>
    <span class="key">予選と本番は切り離す。</span>
    <p>予選の点数は最終順位に持ち込まない。<br>
       AIの点数も順位計算には一切入れない。<br>
       <b>最終順位は本番12名の採点だけで決まる。</b></p>
  </div>

  <div class="hi hi-gold">
    <h3>今日ここで決めること</h3>
    <ul><li>登壇順の決め方</li><li>入力ツールと当日運用</li><li>記録・講評・発表の段取り</li></ul>
  </div>
</div>

<div class="sec sec-navy">
  <div class="band band-navy">全体の流れ（何をいつ決めるか）</div>
  <div class="sec-in">
    <div class="tl"><div class="tl-ico">{ico('cal')}</div>{tl}</div>
  </div>
</div>

<div class="two">
  <div class="sec sec-green">
    <div class="band band-green">A. 役員予備審査（4名）― 決勝に進む4部を決める</div>
    <div class="sec-in">
      <p class="aim"><b>確定</b><span>各役員が上位4部に順位をつけ、合計点で予選順位を出す。
        <em>予選順位は非公開</em></span></p>
      {fig_points()}
      {chk([
        "AIの6観点評価・根拠・強み／弱みを材料に、各自が<b>上位4部に順位</b>をつける",
        "決勝進出は<b>合計点の高い順に上位4部</b>で決める（1位票が1つあるだけの無条件進出はしない）",
        "同点は ①1位票の数 → ②2位票の数 → ③AI予備審査点 → ④事務局・役員の合議 で決める",
        "資料は<b>部門名の五十音順</b>で配布する（AI点順に並べない）",
      ])}
      <p class="note push">1位10点／2位8点は差が2点だが、4位6点と5位0点の差は6点。
        つまり「4位以内に入るだけ」で下駄が大きい。同点タイブレークで1位票の数を最優先にしているのは、
        票が割れやすい尖った応募（上坂さんの「粗削りでも兆し」、前田さんの「遊びから生まれたものでも」）を
        僅差の場面で拾い上げるため。ただし無条件の保護ではなく、あくまで合計点が並んだときの優先順位。</p>
    </div>
  </div>

  <div class="sec sec-blue">
    <div class="band band-blue">B. 本番審査（12名・スタジオ）― 最終順位を決める</div>
    <div class="sec-in">
      <p class="aim"><b>確定</b><span>各部を100点満点で採点し、最高・最低を除外した10名の平均で順位を確定する
        <em>（合議による順位変更なし）</em></span></p>
      {chk([
        "各審査員が<b>4部それぞれを100点満点</b>で採点する",
        "<b>最高点と最低点を各1つずつ除外</b>し、残り10名の平均で確定",
        "同値が複数あっても<b>除外は1つだけ</b>（全部除くと母数が減りすぎる）",
        "<b>4部すべてを採点した人のみ有効</b>。途中退席者の採点は全部無効",
        "平均は<b>小数第2位</b>まで（第1位だと同点が出やすい）",
        "予選の点数は加算しない。<b>最終順位は本番の点数だけ</b>で決まる",
      ])}
      <div class="sec sec-blue push" style="border-width:0.09cqw">
        <div class="sec-in" style="background:var(--blu-s);gap:0.4cqw">
          <p class="sub-h" style="color:var(--blu)">当日の流れ</p>
          <div class="flow">
            <div class="flow-step"><b>4部が順にプレゼン</b></div>
            <span class="flow-arw">→</span>
            <div class="flow-step"><b>各プレゼン直後に入力</b><span>後半有利を防ぐ</span></div>
            <span class="flow-arw">→</span>
            <div class="flow-step"><b>終了後に修正2分</b><span>前半の辛さを補正</span></div>
            <span class="flow-arw">→</span>
            <div class="flow-step"><b>最高・最低を除外</b><span>して平均算出</span></div>
            <span class="flow-arw">→</span>
            <div class="flow-step" style="border-color:var(--gold);background:var(--gold-s)">
              {ico('cup', 'ico-sm', '#8A6300')}<b style="color:var(--gold)">最終順位を発表・表彰</b></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="pre pre-org">
  <div class="pre-lab">C.<br>まだ<br>決まって<br>いないこと</div>
  <div class="pre-body" style="align-items:stretch">
    {cards(C, 'n', 5)}
  </div>
</div>

<div class="goal">
  <div class="goal-lab">{ico('bulb', 'ico-sm')} この会議のゴール</div>
  <p>上記 C の5項目を確定し、9/4の役員4名向け配布資料と、9/15当日の運用マニュアルに落とし込むこと</p>
</div>

</div></div></div>
"""

if __name__ == "__main__":
    out = pathlib.Path(__file__).parent / "審査設計ボード_決定版.html"
    out.write_text(HTML, encoding="utf-8")
    print(out.name, len(HTML), "chars")
