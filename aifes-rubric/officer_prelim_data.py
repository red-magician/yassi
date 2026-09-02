# -*- coding: utf-8 -*-
"""
役員予備審査ツール（HTML版）の唯一の定義元。

Excel「04_役員予備審査投票」シートとは完全に独立したツール（2026-08-27 合意）。
役員4名それぞれに個別配布する採点ページと、集計係が使う集計ページを
build_officer_prelim_tool.py が生成する。

役員は「選ぶ」「書く」だけ。AI予備審査の結果（後述のAI_SCORE_XLSXから転記）を
参考値として見た上で、役員が人間の判断として1〜4位を選ぶ。
Copilot連携・審査員別ペルソナ文書は今回は用意しない（合意事項）。
"""

# ---------------------------------------------------------------------------
# 役員4名（実名）。グランドフィナーレ12名審査員のうちの4名が兼務。
# ---------------------------------------------------------------------------
OFFICERS = [
    dict(key="officer1", name="伊藤 裕一"),
    dict(key="officer2", name="伊藤 英啓"),
    dict(key="officer3", name="小杉 智"),
    dict(key="officer4", name="松尾 邦孝"),
]

# ---------------------------------------------------------------------------
# 役員予備審査の投票→点数変換と、同点になったときの優先順位。
# 集計ツール（build_officer_prelim_tool.py の TALLY_JS）はこの並び順で
# タイブレークキーを組み立てている。文言を変えたらコードの並びも合わせること。
# ---------------------------------------------------------------------------
POINTS_BY_RANK = {1: 10, 2: 8, 3: 7, 4: 6}

TIEBREAK_OFFICER = [
    "合計点（1位×10 + 2位×8 + 3位×7 + 4位×6）が高い方を上位とする",
    "1位に選んだ役員の人数が多い方を上位とする",
    "2位に選んだ役員の人数が多い方を上位とする",
    "AI予備審査の点数（3回採点の平均）が高い方を上位とする",
    "それでも並ぶ場合は、事務局・役員の合議で決定する",
]

# ---------------------------------------------------------------------------
# グランドフィナーレ 決勝進出候補（予備審査の対象）。全13件、実データ。
# 出典：AIFES2026_グランドフィナーレAI予備審査（3回採点・監査ログ付き）.xlsx
#   ①最終結果 / ⑤応募元リンク一覧 / ⑥採点遷移・監査ログ　各シートより転記。
# avg・band はAIが同じ内容を3回独立採点した平均・判定（S/A/B/C）。
# note は監査ログの「変更概要」＝採点時にAIが実際に確認した根拠の要約。
# ---------------------------------------------------------------------------
GF_ENTRIES = [
    dict(
        code='GRANDFINALE-2026-000012', dept='CMS本部 沖縄事業所', title='人の可能性を信じているからこそ_私たちはAIをサービスにして_AIを仕組化する',
        submitter='Goya, Saki', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=499&stage=grandFinale',
        r1=90, r2=90, r3=98, avg=92.7, band='S',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000017', dept='AIX本部 AIセールス部', title='マルチAIの徹底活用による提案プロセスBPRの事業成果！',
        submitter='Kaga, Yuji', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=528&stage=grandFinale',
        r1=76, r2=76, r3=84, avg=78.7, band='A',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000008', dept='製造事業本部 CS2部', title='AIを使う本部からAIで顧客価値を生む本部へ~製造事業本部が挑んだ変化のストーリー~',
        submitter='Hosomizu, Hiroki', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=482&stage=grandFinale',
        r1=68, r2=68, r3=72, avg=69.3, band='A',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000025', dept='ネクストスケープ', title='AIの話が自然に集まる場所を、会社の中につくった',
        submitter='Yanai, Masahiro', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=581&stage=grandFinale',
        r1=66, r2=66, r3=68, avg=66.7, band='A',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000028', dept='トヨタ事業本部 CI部', title='AIを仲間に、人がやるべき仕事を人に取り戻す',
        submitter='Mizutani, Tomoaki', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=588&stage=grandFinale',
        r1=66, r2=64, r3=70, avg=66.7, band='A',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000020', dept='GRC本部 法務・コンプライアンス部', title='現場主導でAIを育てる＿AI育成・改善の現場実践・活用モデル',
        submitter='Kakishima, Naoki', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=532&stage=grandFinale',
        r1=64, r2=66, r3=68, avg=66, band='A',
        ai_note='PDF全文確認で、1～10営業日→15～20分のBPR、全社スキル化を確認。+19.3点。',
    ),
    dict(
        code='GRANDFINALE-2026-000026', dept='ERP（US）', title='Expense System 再構築 － ユーザー駆動自動開発',
        submitter='Hiroyuki Tomomasa', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=586&stage=grandFinale',
        r1=66, r2=66, r3=66, avg=66, band='A',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000024', dept='CMS本部 MSC', title='MSCの現場知見をAIにつなぎ、お客様価値と事業成長へ',
        submitter='Hamada, Kentaro', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=577&stage=grandFinale',
        r1=64, r2=62, r3=64, avg=63.3, band='B',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000005', dept='HR戦略本部 人材開発部', title='AIで生んだ時間を、人を育てる時間に変えた。',
        submitter='Ochi, Kazumi', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=438&stage=grandFinale',
        r1=60, r2=60, r3=58, avg=59.3, band='B',
        ai_note='PDFで残業約31%減、約42時間削減を確認。評価根拠を補強。',
    ),
    dict(
        code='GRANDFINALE-2026-000014', dept='HR戦略本部 人事部', title='猫の手も借りたい人事部、AIの手を借りることにした。',
        submitter='Katsumata, Yumi', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=522&stage=grandFinale',
        r1=60, r2=56, r3=60, avg=58.7, band='B',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000016', dept='HR戦略本部 採用センター 新卒採用課', title='面接もインターンシップも、Copilotが標準装備の新卒採用チームへ。',
        submitter='Yamanouchi, Yurie', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=527&stage=grandFinale',
        r1=58, r2=58, r3=54, avg=56.7, band='B',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000015', dept='ホンダ事業本部', title='AIフロンティア～AI実践による事業変革と競争力強化への挑戦～',
        submitter='Yoshizawa, Hirokazu', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=525&stage=grandFinale',
        r1=50, r2=50, r3=48, avg=49.3, band='C',
        ai_note='HTML→PDFは本文欠落。原本PPTXで全文確認しC3/C4を上方修正。',
    ),
    dict(
        code='GRANDFINALE-2026-000023', dept='ME事業本部', title='PptxGenJS Presentation',
        submitter='Akiyama, Masamichi', primary='https://jbsaisummerfestival.z11.web.core.windows.net/pages/viewer.html?entry=576&stage=grandFinale',
        r1=42, r2=46, r3=44, avg=44, band='C',
        ai_note='PPTX/PDFでL1評価中・L4検討中・L6構想段階を確認。F3を裏付け。',
    ),
]
