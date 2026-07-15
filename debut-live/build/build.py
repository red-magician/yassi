import re, os

HERE = os.path.dirname(os.path.abspath(__file__))
sjs = open(os.path.join(HERE, 'package/dist/xlsx.mini.min.js'), encoding='utf-8').read()
dist_dir = os.path.join(HERE, '..', 'dist')
os.makedirs(dist_dir, exist_ok=True)

TARGETS = [
    ('template.html', 'AIFES2026_デビューライブ_受賞選定ツール.html'),
    ('template_reconcile.html', 'AIFES2026_デビューライブ_受賞突合ツール.html'),
]

for src_name, out_name in TARGETS:
    tpl = open(os.path.join(HERE, src_name), encoding='utf-8').read()
    out = tpl.replace('__SHEETJS__', sjs)
    assert not re.findall(r'__[A-Z_]+__', out), f'{src_name}: 未置換のプレースホルダが残っています'
    out_path = os.path.join(dist_dir, out_name)
    open(out_path, 'w', encoding='utf-8').write(out)
    print('生成:', out_path, f'({len(out):,} bytes)')
