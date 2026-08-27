# -*- coding: utf-8 -*-
"""
役員予備審査ツール（HTML版）の唯一の定義元。

Excel「04_役員予備審査投票」シートとは完全に独立したツール（2026-08-27 合意）。
役員4名それぞれに個別配布する採点ページと、集計係が使う集計ページを
build_officer_prelim_tool.py が生成する。

役員は「選ぶ」「書く」だけ。点数はAI予備審査（rubric_data.py）がすでに出したものを
そのまま参照値として見せる。役員はそれを見た上で人間の判断として1〜4位を選ぶ。
Copilot連携・審査員別ペルソナ文書は今回は用意しない（合意事項）。
"""

from rubric_data import CRITERIA, WEIGHTS, BANDS

# ---------------------------------------------------------------------------
# 役員4名。氏名は未確定のため仮名。決定次第ここを差し替えれば全ファイルに反映される。
# ---------------------------------------------------------------------------
OFFICERS = [
    dict(key="officer1", name="役員A（仮）"),
    dict(key="officer2", name="役員B（仮）"),
    dict(key="officer3", name="役員C（仮）"),
    dict(key="officer4", name="役員D（仮）"),
]

# ---------------------------------------------------------------------------
# グランドフィナーレ決勝進出候補（予備審査の対象）。
# 6観点のレベルは 0=未評価, 1〜5（5が最高）。AI予備審査の結果をそのまま転記する。
# 人材開発部のみ実データ・実採点済み。残りは応募が揃い次第、同じ形式で追記する。
# ---------------------------------------------------------------------------
GF_ENTRIES = [
    dict(
        code="GRANDFINALE-2026-000005",
        dept="HR戦略本部 人材開発部",
        title="AIで生んだ時間を、人を育てる時間に変えた。",
        submitter="Ochi, Kazumi",
        primary="（本文はSharePoint上のHTML提出物）",
        procedure="補足資料①：施策補足資料 / 補足資料②：新入社員のAIについての反応まとめ",
        levels={"C1": 3, "C2": 4, "C3": 3, "C4": 4, "C5": 3, "C6": 3},
        ai_note=(
            "F2（特定個人1名の成果）は「全員で取り組んだ」との確認により解除。"
            "C6は人材開発部の性質上、育成した人材が他部門へ配属されることによる波及を"
            "今回に限り加点材料として考慮（配属後の追跡データはまだ本文になし）。"
        ),
        gaps=[],
    ),
    # --- 以下、応募が揃い次第この形式で追加 ---
    # dict(code="GRANDFINALE-2026-0000XX", dept="", title="", submitter="",
    #      primary="", procedure="", levels={"C1":0,"C2":0,"C3":0,"C4":0,"C5":0,"C6":0},
    #      ai_note="", gaps=[]),
] + [
    dict(
        code=f"DEMO-2026-{i:03d}", dept=f"【デモ】{dept}", title=title, submitter="（ダミー）",
        primary=primary, procedure=procedure,
        levels=levels, ai_note="※動作確認用のダミーエントリーです。実際の応募内容ではありません（リンク先は集計ツールの実データを流用しているため開けます）。",
        gaps=[], demo=True,
    )
    for i, (dept, title, levels, primary, procedure) in enumerate([
        ("DXソリューション本部", "全社基盤化した申請AIエージェント", {"C1": 5, "C2": 4, "C3": 4, "C4": 4, "C5": 4, "C6": 5},
         "https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/SoloSubmissions/%E3%82%BD%E3%83%AD%E3%83%A9%E3%82%A4%E3%83%96%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E8%84%B1%E3%83%BBCopilot%20Studio%E5%AE%A3%E8%A8%80.html",
         "https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/SoloSubmissions/%E3%82%BD%E3%83%AD%E3%83%A9%E3%82%A4%E3%83%96%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E6%89%8B%E9%A0%86%E6%9B%B8_%E6%89%8B%E9%A0%86%E6%9B%B8%20(2).html"),
        ("カスタマーサクセス部", "問い合わせ一次対応をAIで再設計", {"C1": 4, "C2": 4, "C3": 3, "C4": 3, "C5": 3, "C6": 4},
         "https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/SoloSubmissions/%E3%82%BD%E3%83%AD%E3%83%A9%E3%82%A4%E3%83%96%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/ai-fes-explanation.html",
         "https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/SoloSubmissions/%E3%82%BD%E3%83%AD%E3%83%A9%E3%82%A4%E3%83%96%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/ai-fes-procedure%20(1).html"),
        ("ファイナンス統括部", "月次決算資料の下書きをAIで生成", {"C1": 3, "C2": 3, "C3": 2, "C4": 3, "C5": 2, "C6": 3},
         "https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/CollabSubmissions/%E3%82%B3%E3%83%A9%E3%83%9C%E3%82%A2%E3%82%AF%E3%83%88%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E8%AA%AC%E6%98%8E%E8%B3%87%E6%96%99.html",
         "https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/CollabSubmissions/%E3%82%B3%E3%83%A9%E3%83%9C%E3%82%A2%E3%82%AF%E3%83%88%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E5%B0%86%E6%9D%A5%E5%83%8F.png"),
        ("マーケティング推進部", "生成AIでの訴求文言A/Bテスト運用", {"C1": 2, "C2": 2, "C3": 2, "C4": 2, "C5": 1, "C6": 2},
         "https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/SoloSubmissions/%E3%82%BD%E3%83%AD%E3%83%A9%E3%82%A4%E3%83%96%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/yamane-fes.html",
         "https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/SoloSubmissions/%E3%82%BD%E3%83%AD%E3%83%A9%E3%82%A4%E3%83%96%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E6%89%8B%E9%A0%86%E6%9B%B8_%E6%89%8B%E9%A0%86%E6%9B%B8%20(1)%20(3).html"),
        ("プロダクト開発部", "レビュー観点をAIで自動チェック", {"C1": 3, "C2": 3, "C3": 2, "C4": 2, "C5": 2, "C6": 3},
         "https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/SoloSubmissions/%E3%82%BD%E3%83%AD%E3%83%A9%E3%82%A4%E3%83%96%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E3%80%90%E6%9C%AC%E7%95%AA%E4%BD%9C%E6%A5%AD%E3%83%AC%E3%83%93%E3%83%A5%E3%83%BC%E8%A3%9C%E5%8A%A9%E3%82%A8%E3%83%BC%E3%82%B8%E3%82%A7%E3%83%B3%E3%83%88%E3%80%91AI%20%E3%81%AB%E3%82%88%E3%82%8B%E4%BA%8B%E5%89%8D%E3%83%AC%E3%83%93%E3%83%A5%E3%83%BC%E3%81%A7%E3%83%AC%E3%83%93%E3%83%A5%E3%83%BC%E5%93%81%E8%B3%AA%E3%82%92%E5%BA%95%E4%B8%8A%E3%81%92.html",
         "https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/SoloSubmissions/%E3%82%BD%E3%83%AD%E3%83%A9%E3%82%A4%E3%83%96%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E6%9C%AC%E7%95%AA%E3%83%AC%E3%83%93%E3%83%A5%E3%83%BC%E8%A3%9C%E5%8A%A9%E3%82%A8%E3%83%BC%E3%82%B8%E3%82%A7%E3%83%B3%E3%83%88%E5%88%A9%E7%94%A8%E6%89%8B%E9%A0%86.pdf"),
    ], start=1)
]


def ai_total(entry):
    """レベル(1-5)×配点/5 の合計。levelsが0（未評価）の観点は0点扱い。"""
    total = 0
    for c in CRITERIA:
        lv = entry["levels"].get(c["id"], 0)
        total += c["weight"] * lv / 5
    return round(total)


def ai_band(total):
    for lo, label, _desc in BANDS:
        if total >= lo:
            return label
    return "C"
