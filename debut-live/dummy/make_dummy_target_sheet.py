# 実際のポータルエクスポート形式（シート名「対象者」、列名が SubmitterDisplayName ではなく
# 投稿者／所属／LikeCount／投稿者LikesGiven件数（全競技）など）を模したダミーデータ。
# 実データは含まない（氏名・部署はすべて架空）。
#
# 「対象者」シートの他に、同じワークブックに全件版の「◯◯_エントリー別いいね」シートも入れて、
# 行数の多い方（全件版）ではなく「対象者」シートが優先的に選ばれることを回帰テストで確認する。
import openpyxl, os

HERE = os.path.dirname(os.path.abspath(__file__))

HEAD = ['EntryCode','タイトル','競技','CompetitionKey','PeriodKey','投稿者','投稿者メール','所属',
        'PublishedAt','Status','SubmissionStatus','IsHidden','Encore','Buzz','Scene','LikeCount',
        'UniqueUserCount','ReactionRows','最初のいいね日','最後のいいね日',
        '投稿者LikesGiven件数（全競技）','投稿者LikesGiven対象Entry数（全競技）',
        '投稿者自己リアクション数（全競技）','受賞対象外','受賞詳細','いいねした人',
        'PrimaryFileUrl','TeamsPostUrl','GlobalEntryId']

names = [('Yamada, Taro','AIX本部'), ('Sato, Hanako','製造本部 CS1部'), ('Suzuki, Ichiro','金融保険本部 CS4部'),
          ('Takahashi, Misaki','CTS本部 CSA部'), ('Tanaka, Kenta','事業管理本部'), ('Ito, Sakura','通信サービス本部 CS2部'),
          ('Watanabe, Shota','金融本部 営業部'), ('Nakamura, Yui','CBS事業本部 IPA部'), ('Kobayashi, Akari','HR戦略本部 人事部'),
          ('Kato, Daisuke','PA本部 L&PB推進部')]

def row(i, name, dept, *, comp='debut', status='Published', hidden='False', ext='html', has_link=True, likes=20, given=30):
    code = f'DEBUT-2026-{i:06d}'
    url = f'https://example.com/DebutSubmissions/entry-{i}.{ext}' if has_link else ''
    return [code, f'ダミー投稿{i}', 'デビューライブ', comp, 'debut-cool3', name, f'{name.lower()}@example.com', dept,
            None, status, status, hidden, True, False, False, likes, likes, likes, None, None,
            given, given, 0, None, None, '', url, None, f'hackathon2026-debut-item-{i}']

rows = []
for i, (name, dept) in enumerate(names, start=1):
    likes = [12, 25, 18, 30, 5, 22, 14, 27, 9, 33][i-1]
    given = [40, 10, 60, 0, 20, 45, 5, 70, 15, 25][i-1]
    rows.append(row(i, name, dept, likes=likes, given=given))

# 10件目は他競技（除外されるべき）
rows[9] = row(10, *names[9], comp='solo', likes=99, given=99)
# 9件目は非公開（除外されるべき）
rows[8] = row(9, *names[8], hidden='True', likes=1, given=1)
# 8件目は下書き（Published以外・除外されるべき）
rows[7] = row(8, *names[7], status='Draft', likes=1, given=1)
# 7件目は作品リンク未提出（資料欠損）
rows[6] = row(7, *names[6], has_link=False, likes=7, given=7)
# 6件目はMarkdown提出（HTML加点なし）
rows[5] = row(6, *names[5], ext='md', likes=22, given=45)

wb = openpyxl.Workbook()
ws = wb.active
ws.title = '対象者'
ws.append(HEAD)
for r in rows: ws.append(r)

# 同じワークブックに、行数の多い「全件版」シートも入れておく（対象者シートが優先されるかの確認用）
ws_all = wb.create_sheet('デビューライブ_ダミー_エントリー別いいね')
ws_all.append(HEAD)
for r in rows: ws_all.append(r)
# 全件版だけに、対象者シートには無い追加1件を混ぜて行数を多くする
ws_all.append(row(11, 'Extra, Person', '他本部', likes=1, given=1))

path = os.path.join(HERE, 'master_target_sheet.xlsx')
wb.save(path)
print('生成:', path)
print('対象者シート件数（除外3件含む）:', len(rows), '／ 全件版シート件数:', len(rows) + 1)
