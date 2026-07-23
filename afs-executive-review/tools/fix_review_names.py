#!/usr/bin/env python3
"""
AI講評（役員エージェント講評）の文中に、採点時の審査員名がそのまま埋め込まれている場合に
汎用的な「あなた」へ置き換える。

背景: 同じ競技を複数名の役員が担当する場合、採点結果Excel（10_役員向け審査シート）は
1本を全員の役員ファイルに共通で取り込む。そのため講評文中に「最終判断は◯◯さんご自身へ」の
ように特定の審査員名が入っていると、別の役員のファイルを開いたときに名前が一致しなくなる。

対象の実名リストはこのスクリプトには含めない（実データのため git 管理外）。
names.txt に1行1名で審査員名を列挙し、--names で渡す。

使い方:
  python3 tools/fix_review_names.py --names names.txt dist/*.html
"""
import re
import json
import sys
import argparse


def build_pattern(names):
    # 姓と名の間にスペースが入っている表記ゆれ（例：「中村 智之」）も拾えるようにする
    parts = []
    for n in names:
        n = n.strip()
        if not n:
            continue
        spaced = r'\s*'.join(re.escape(ch) for ch in n)
        parts.append(spaced)
    if not parts:
        raise SystemExit("置換対象の名前が1件もありません（--names で指定してください）")
    return re.compile(r'(?:' + '|'.join(parts) + r')\s*さん')


def fix_file(path, pattern):
    html = open(path, encoding="utf-8").read()
    m = re.search(r'let aiData = (\{.*?\});', html, re.S)
    if not m:
        print(path, ": aiData が見つかりません（スキップ）")
        return
    data = json.loads(m.group(1))
    changed = 0
    for d in data.values():
        review = d.get('review', '') or ''
        new_review, n = pattern.subn('あなた', review)
        if n:
            d['review'] = new_review
            changed += n
    if changed:
        new_block = json.dumps(data, ensure_ascii=False)
        new_html = html[:m.start(1)] + new_block + html[m.end(1):]
        open(path, "w", encoding="utf-8").write(new_html)
        print(path, f": {changed}箇所を「あなた」に置換")
    else:
        print(path, ": 該当なし")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument('--names', required=True, help='審査員の実名を1行1名で列挙したテキストファイル')
    ap.add_argument('files', nargs='+', help='対象HTML')
    args = ap.parse_args()

    with open(args.names, encoding='utf-8') as f:
        names = [line.strip() for line in f if line.strip()]
    pattern = build_pattern(names)

    for p in args.files:
        fix_file(p, pattern)
