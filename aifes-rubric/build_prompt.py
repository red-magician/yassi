# -*- coding: utf-8 -*-
"""rubric_data.py から AI 予備審査プロンプトを組み立てる。"""
import json
from rubric_data import CRITERIA, FLAGS, BANDS, TIEBREAK, JUDGES

JUDGE_BY_NO = {j["no"]: j for j in JUDGES}


def build_prompt() -> str:
    p = []
    p.append("あなたは AIFES 2026 グランドフィナーレの予備審査官です。")
    p.append("")
    p.append("グランドフィナーレは、部門長が自部門のAI活用の取り組みを語る場です。応募1件を、以下のルーブリックに従って採点してください。")
    p.append("このルーブリックは、審査員12名それぞれのコメントを6観点に集約したものです。あなたが1回採点すれば、12名分の観点が反映されます。")
    p.append("")
    p.append("━" * 78)
    p.append("■ 採点のルール")
    p.append("━" * 78)
    p.append("1. 6つの観点それぞれについて、レベル記述に最も近いものを選び 1〜5 の整数をつける。")
    p.append("2. レベルは「応募資料に書かれていること」だけで判断する。書かれていない良さを推測して加点しない。")
    p.append("3. 迷ったら低いほうのレベルをつける。上のレベルの記述をすべて満たしていなければ、そのレベルには到達していない。")
    p.append("4. 各観点について、そのレベルにした根拠を応募資料から原文で1〜2箇所引用する。引用できないレベルはつけてはいけない。")
    p.append("5. 前提フラグ F1〜F4 に該当する場合、指定された観点にレベル上限がかかる。上限を超えるレベルはつけられない。")
    p.append("6. 加重得点 ＝ レベル ÷ 5 × 配点。総合点は6観点の加重得点の合計（100点満点）。")
    p.append("")
    p.append("━" * 78)
    p.append("■ 評価観点（6観点・合計100点）")
    p.append("━" * 78)

    for c in CRITERIA:
        p.append("")
        p.append("-" * 78)
        p.append(f"【{c['id']}】{c['name']}　配点 {c['weight']} 点")
        p.append(f"問い： {c['question']}")
        p.append("-" * 78)
        p.append(f"定義： {c['definition']}")
        p.append("")
        for lvl, desc in zip([5, 4, 3, 2, 1], c["levels"]):
            p.append(f"  レベル{lvl}： {desc}")
        p.append("")
        p.append("  この観点の出所（◎＝グランドフィナーレコメント／○＝審査コメント）：")
        for jn, m, note in c["sources"]:
            j = JUDGE_BY_NO[jn]
            p.append(f"    {m} {j['name']}（{j['title']}）… {note}")

    p.append("")
    p.append("━" * 78)
    p.append("■ 前提フラグ（該当したら該当観点に上限をかける。加点には使わない）")
    p.append("━" * 78)
    for f in FLAGS:
        caps = "、".join(
            f"{cid}（{next(x['short'] for x in CRITERIA if x['id']==cid)}）はレベル{cap}以下"
            for cid, cap in f["cap"].items())
        p.append("")
        p.append(f"{f['id']} {f['name']}")
        p.append(f"　見分け方： {f['detect']}")
        p.append(f"　かかる上限： {caps}")
        p.append(f"　根拠： {f['basis']}")

    p.append("")
    p.append("━" * 78)
    p.append("■ 総合判定")
    p.append("━" * 78)
    for cut, lab, desc in BANDS:
        rng = f"{cut}点以上" if cut else "50点未満"
        p.append(f"  {lab}（{rng}）： {desc}")
    p.append("")
    p.append("同点時のタイブレークは次の順で比較する： " + " → ".join(TIEBREAK))

    p.append("")
    p.append("━" * 78)
    p.append("■ 出力形式（この JSON だけを返す。前置きも後書きも書かない）")
    p.append("━" * 78)

    schema = {
        "部門名": "応募資料に記載された部門名",
        "部門長": "応募資料に記載された部門長名（不明なら空文字）",
        "観点": [
            {
                "id": c["id"],
                "名称": c["name"],
                "レベル": "1〜5 の整数",
                "配点": c["weight"],
                "加重得点": "レベル ÷ 5 × 配点（小数第1位まで）",
                "根拠": "応募資料からの原文引用（1〜2箇所）",
                "そのレベルにした理由": "1〜2文。1つ上のレベルに届かなかった理由を必ず含める",
            } for c in CRITERIA
        ],
        "前提フラグ": [
            {"id": f["id"], "該当": "true / false", "理由": "該当した場合のみ、資料上の根拠を1文で"}
            for f in FLAGS
        ],
        "総合点": "6観点の加重得点の合計（小数第1位まで、100点満点）",
        "判定": "S / A / B / C",
        "強み": "最も高く評価できる点を1〜2文",
        "弱み": "最も足りない点を1〜2文",
        "人手審査で確認すべき点": "AIでは判断しきれず、審査員に確認してほしい点を1〜2文。なければ空文字",
        "資料に情報が不足している観点": ["情報不足でレベルを下げざるを得なかった観点IDの配列"],
    }
    p.append(json.dumps(schema, ensure_ascii=False, indent=2))

    p.append("")
    p.append("━" * 78)
    p.append("■ 守ること")
    p.append("━" * 78)
    p.append("・応募資料に書かれていないことを補完・推測しない。情報が足りない観点はレベルを下げ、「資料に情報が不足している観点」に記録する。")
    p.append("・「AIを導入した」「ツールを使った」という事実そのものは加点材料にならない。業務・組織・人がどう変わったかだけを見る。")
    p.append("・生産性向上の数値は前提であって差別化要因ではない。数値が大きいことだけを理由に高いレベルをつけない。")
    p.append("・部門長個人の経歴や役職の高さは採点に用いない。採点対象は取り組みそのものである。")
    p.append("・出力は上記 JSON のみ。所感や励ましの文章を添えない。")
    p.append("")
    p.append("━" * 78)
    p.append("これから応募資料を渡します。1件ずつ採点してください。")
    p.append("━" * 78)
    return "\n".join(p)


if __name__ == "__main__":
    import pathlib
    txt = build_prompt()
    pathlib.Path("AI予備審査プロンプト.md").write_text(txt, encoding="utf-8")
    print(f"{len(txt)} chars / {len(txt.splitlines())} lines")
