import re, os

HERE = os.path.dirname(os.path.abspath(__file__))
tpl = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
sjs = open(os.path.join(HERE, 'package/dist/xlsx.mini.min.js'), encoding='utf-8').read()

out = tpl.replace('__SHEETJS__', sjs)
assert not re.findall(r'__[A-Z_]+__', out), '未置換のプレースホルダが残っています'

dist_dir = os.path.join(HERE, '..', 'dist')
os.makedirs(dist_dir, exist_ok=True)
out_path = os.path.join(dist_dir, 'AIFES2026_デビューライブ_受賞選定ツール.html')
open(out_path, 'w', encoding='utf-8').write(out)
print('生成:', out_path, f'({len(out):,} bytes)')
