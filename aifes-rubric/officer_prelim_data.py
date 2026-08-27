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
