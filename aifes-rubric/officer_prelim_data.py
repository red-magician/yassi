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
        submitter='Goya, Saki', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E4%BA%BA%E3%81%AE%E5%8F%AF%E8%83%BD%E6%80%A7%E3%82%92%E4%BF%A1%E3%81%98%E3%81%A6%E3%81%84%E3%82%8B%E3%81%8B%E3%82%89%E3%81%93%E3%81%9D_%E7%A7%81%E3%81%9F%E3%81%A1%E3%81%AFAI%E3%82%92%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9%E3%81%AB%E3%81%97%E3%81%A6_AI%E3%82%92%E4%BB%95%E7%B5%84%E5%8C%96%E3%81%99%E3%82%8B.html',
        r1=90, r2=90, r3=98, avg=92.7, band='S',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000017', dept='AIX本部 AIセールス部', title='マルチAIの徹底活用による提案プロセスBPRの事業成果！',
        submitter='Kaga, Yuji', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E3%83%9E%E3%83%AB%E3%83%81AI%E3%81%AE%E5%BE%B9%E5%BA%95%E6%B4%BB%E7%94%A8%E3%81%AB%E3%82%88%E3%82%8B%E6%8F%90%E6%A1%88%E3%83%97%E3%83%AD%E3%82%BB%E3%82%B9BPR%E3%81%AE%E4%BA%8B%E6%A5%AD%E6%88%90%E6%9E%9C%EF%BC%81.html',
        r1=76, r2=76, r3=84, avg=78.7, band='A',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000008', dept='製造事業本部 CS2部', title='AIを使う本部からAIで顧客価値を生む本部へ~製造事業本部が挑んだ変化のストーリー~',
        submitter='Hosomizu, Hiroki', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/AI%E3%82%92%E4%BD%BF%E3%81%86%E6%9C%AC%E9%83%A8%E3%81%8B%E3%82%89AI%E3%81%A7%E9%A1%A7%E5%AE%A2%E4%BE%A1%E5%80%A4%E3%82%92%E7%94%9F%E3%82%80%E6%9C%AC%E9%83%A8%E3%81%B8~%E8%A3%BD%E9%80%A0%E4%BA%8B%E6%A5%AD%E6%9C%AC%E9%83%A8%E3%81%8C%E6%8C%91%E3%82%93%E3%81%A0%E5%A4%89%E5%8C%96%E3%81%AE%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AA%E3%83%BC~.html',
        r1=68, r2=68, r3=72, avg=69.3, band='A',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000025', dept='ネクストスケープ', title='AIの話が自然に集まる場所を、会社の中につくった',
        submitter='Yanai, Masahiro', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/AI%E3%81%AE%E8%A9%B1%E3%81%8C%E8%87%AA%E7%84%B6%E3%81%AB%E9%9B%86%E3%81%BE%E3%82%8B%E5%A0%B4%E6%89%80%E3%82%92%E3%80%81%E4%BC%9A%E7%A4%BE%E3%81%AE%E4%B8%AD%E3%81%AB%E3%81%A4%E3%81%8F%E3%81%A3%E3%81%9F.html',
        r1=66, r2=66, r3=68, avg=66.7, band='A',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000028', dept='トヨタ事業本部 CI部', title='AIを仲間に、人がやるべき仕事を人に取り戻す',
        submitter='Mizutani, Tomoaki', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E3%83%88%E3%83%A8%E3%82%BF%E6%9C%AC%E9%83%A8CI%E9%83%A8_%E3%82%AF%E3%82%99%E3%83%A9%E3%83%B3%E3%83%88%E3%82%99%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC.html',
        r1=66, r2=64, r3=70, avg=66.7, band='A',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000020', dept='GRC本部 法務・コンプライアンス部', title='現場主導でAIを育てる＿AI育成・改善の現場実践・活用モデル',
        submitter='Kakishima, Naoki', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E7%8F%BE%E5%A0%B4%E4%B8%BB%E5%B0%8E%E3%81%A7AI%E3%82%92%E8%82%B2%E3%81%A6%E3%82%8B%EF%BC%BFAI%E8%82%B2%E6%88%90%E3%83%BB%E6%94%B9%E5%96%84%E3%81%AE%E7%8F%BE%E5%A0%B4%E5%AE%9F%E8%B7%B5%E3%83%BB%E6%B4%BB%E7%94%A8%E3%83%A2%E3%83%87%E3%83%AB.html',
        r1=64, r2=66, r3=68, avg=66, band='A',
        ai_note='PDF全文確認で、1～10営業日→15～20分のBPR、全社スキル化を確認。+19.3点。',
    ),
    dict(
        code='GRANDFINALE-2026-000026', dept='ERP（US）', title='Expense System 再構築 － ユーザー駆動自動開発',
        submitter='Hiroyuki Tomomasa', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/AIFES2026_GRANDFINALE_%E5%BF%9C%E5%8B%9F%E8%B3%87%E6%96%99_Expense%E8%87%AA%E5%8B%95%E9%96%8B%E7%99%BA.html',
        r1=66, r2=66, r3=66, avg=66, band='A',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000024', dept='CMS本部 MSC', title='MSCの現場知見をAIにつなぎ、お客様価値と事業成長へ',
        submitter='Hamada, Kentaro', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/MSC%E3%81%AE%E7%8F%BE%E5%A0%B4%E7%9F%A5%E8%A6%8B%E3%82%92AI%E3%81%AB%E3%81%A4%E3%81%AA%E3%81%8E%E3%80%81%E3%81%8A%E5%AE%A2%E6%A7%98%E4%BE%A1%E5%80%A4%E3%81%A8%E4%BA%8B%E6%A5%AD%E6%88%90%E9%95%B7%E3%81%B8.html',
        r1=64, r2=62, r3=64, avg=63.3, band='B',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000005', dept='HR戦略本部 人材開発部', title='AIで生んだ時間を、人を育てる時間に変えた。',
        submitter='Ochi, Kazumi', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/grandfinale_entry_HRD.html',
        r1=60, r2=60, r3=58, avg=59.3, band='B',
        ai_note='PDFで残業約31%減、約42時間削減を確認。評価根拠を補強。',
    ),
    dict(
        code='GRANDFINALE-2026-000014', dept='HR戦略本部 人事部', title='猫の手も借りたい人事部、AIの手を借りることにした。',
        submitter='Katsumata, Yumi', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E7%8C%AB%E3%81%AE%E6%89%8B%E3%82%82%E5%80%9F%E3%82%8A%E3%81%9F%E3%81%84%E4%BA%BA%E4%BA%8B%E9%83%A8%E3%80%81AI%E3%81%AE%E6%89%8B%E3%82%92%E5%80%9F%E3%82%8A%E3%82%8B%E3%81%93%E3%81%A8%E3%81%AB%E3%81%97%E3%81%9F%E3%80%82.html',
        r1=60, r2=56, r3=60, avg=58.7, band='B',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000016', dept='HR戦略本部 採用センター 新卒採用課', title='面接もインターンシップも、Copilotが標準装備の新卒採用チームへ。',
        submitter='Yamanouchi, Yurie', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E9%9D%A2%E6%8E%A5%E3%82%82%E3%82%A4%E3%83%B3%E3%82%BF%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%83%E3%83%97%E3%82%82%E3%80%81Copilot%E3%81%8C%E6%A8%99%E6%BA%96%E8%A3%85%E5%82%99%E3%81%AE%E6%96%B0%E5%8D%92%E6%8E%A1%E7%94%A8%E3%83%81%E3%83%BC%E3%83%A0%E3%81%B8%E3%80%82.html',
        r1=58, r2=58, r3=54, avg=56.7, band='B',
        ai_note='3回採点後、追加資料による重要な変更なし。',
    ),
    dict(
        code='GRANDFINALE-2026-000015', dept='ホンダ事業本部', title='AIフロンティア～AI実践による事業変革と競争力強化への挑戦～',
        submitter='Yoshizawa, Hirokazu', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/AI%E3%83%95%E3%83%AD%E3%83%B3%E3%83%86%E3%82%A3%E3%82%A2%EF%BD%9EAI%E5%AE%9F%E8%B7%B5%E3%81%AB%E3%82%88%E3%82%8B%E4%BA%8B%E6%A5%AD%E5%A4%89%E9%9D%A9%E3%81%A8%E7%AB%B6%E4%BA%89%E5%8A%9B%E5%BC%B7%E5%8C%96%E3%81%B8%E3%81%AE%E6%8C%91%E6%88%A6%EF%BD%9E.html',
        r1=50, r2=50, r3=48, avg=49.3, band='C',
        ai_note='HTML→PDFは本文欠落。原本PPTXで全文確認しC3/C4を上方修正。',
    ),
    dict(
        code='GRANDFINALE-2026-000023', dept='ME事業本部', title='PptxGenJS Presentation',
        submitter='Akiyama, Masamichi', primary='https://jbsbpos1.sharepoint.com/sites/Guest-JBSAISUMMERFESTIVAL2026/GrandFinaleSubmissions/%E3%82%B0%E3%83%A9%E3%83%B3%E3%83%89%E3%83%95%E3%82%A3%E3%83%8A%E3%83%BC%E3%83%AC%E6%8A%95%E7%A8%BF%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0/%E3%83%AC%E3%82%A4%E3%83%A46%E3%81%AB%E3%82%88%E3%82%8BAI%E5%8D%94%E5%83%8D%E5%9E%8B%E3%82%A2%E3%83%97%E3%83%AA%E3%82%B1%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3%E9%96%8B%E7%99%BA.pptx',
        r1=42, r2=46, r3=44, avg=44, band='C',
        ai_note='PPTX/PDFでL1評価中・L4検討中・L6構想段階を確認。F3を裏付け。',
    ),
]
