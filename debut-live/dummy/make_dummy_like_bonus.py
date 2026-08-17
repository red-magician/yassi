# いいね加点の「相対配点」方式（対象者全員の中で最も多い人を満点(もらう20点/押す40点)とし、
# 他の人はその人との比率で点数がつく。個人ごとの絶対的な上限は無い）を検証するための、
# きりのよい数値だけで作ったダミーデータ。実データは含まない。
import openpyxl, os

HERE = os.path.dirname(os.path.abspath(__file__))

HEAD = ['EntryCode','GlobalEntryId','対象月','応募者・部署','作品リンク','ProcedureFileUrl',
        '観点①スコア','観点②スコア','観点③スコア','観点④スコア',
        '作品ファイル形式','手順書ファイル形式','いいね（もらう）','いいね（押す）','AI講評']

# (name, もらう, 押す)。A=もらうの最多者(100)、B=押すの最多者(200)。もらう・押すの最多者は別人にしてある
# （合算のいいね得点が「両方の最多者」以外は満点にならないことを確認するため）。
rows_data = [
    ('A社員', 100, 0),    # もらう最多 → もらう満点20、押すは0
    ('B社員', 50, 200),   # もらう半分 → 10 ／ 押す最多 → 満点40
    ('C社員', 25, 100),   # もらう1/4 → 5 ／ 押す半分 → 20
    ('D社員', 0, 0),      # どちらも0
]

wb = openpyxl.Workbook()
ws = wb.active
ws.title = '02_採点結果台帳_デビューライブ'
ws.append(HEAD)
for i, (name, likes, likes_given) in enumerate(rows_data, start=1):
    code = f'DEBUT-2026-{i:04d}'
    row = [code, f'GID-{i:05d}', '2026年7月', f'{name}/検証部',
           f'https://example.com/works/{code}', f'https://example.com/proc/{code}',
           8, 8, 8, 8, 'HTML', 'HTML', likes, likes_given, f'{name}のダミー講評']
    ws.append(row)

path = os.path.join(HERE, 'like_bonus_test.xlsx')
wb.save(path)
print('生成:', path)
print('期待値: A=もらう20/押す0 (計20)　B=もらう10/押す40 (計50)　C=もらう5/押す20 (計25)　D=もらう0/押す0 (計0)')
