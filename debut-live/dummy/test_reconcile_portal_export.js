// 集計ツール（3人平均）: 「ポータル掲載データを書き出す」ボタンの回帰テスト
// ポータル班に渡す1シートExcel。階層(ゴールド/シルバー/ブロンズ/ノミネート)・順位・氏名/部署・
// 最終スコア・いいね数・HTML加点・評価コメント・投稿URLだけに絞られていて、内部項目が入らないこと
const { chromium } = require('playwright');
const path = require('path');
const { execSync } = require('child_process');
const assert = require('assert');
function ok(c, m) { assert(c, 'FAIL: ' + m); console.log('OK:', m); }

const TOOL = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_受賞選定ツール.html');
const AGG = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_集計ツール_3人平均.html');
const MASTER = path.resolve(__dirname, 'master_test.xlsx');

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });

  const members = [{ name: '田中', key: 'A', base: 8 }, { name: '佐藤', key: 'B', base: 6 }, { name: '鈴木', key: 'C', base: 10 }];
  const files = [];
  for (const m of members) {
    const p = await b.newPage();
    await p.goto(TOOL);
    await p.fill('#staffName', m.name); await p.fill('#targetMonth', '2026年7月');
    await p.setInputFiles('#fileMaster', MASTER); await p.waitForTimeout(800);
    const codes = await p.evaluate(() => ENTRIES.map(e => e.code));
    const blocks = codes.map((c, i) => {
      const v = Math.max(0, Math.min(10, m.base + (i % 5) - 2));
      return `===SCORE===\nEntryCode: ${c}\n観点①: ${v}\n観点②: ${v}\n観点③: ${v}\n観点④: ${v}\n===END===`;
    }).join('\n\n');
    await p.evaluate((t) => { applyCopilot(t); saveState(); render(); }, blocks);
    await p.evaluate((name) => {
      ENTRIES.forEach(e => {
        notes[e.code] = notes[e.code] || { reason: '', comment: '' };
        notes[e.code].comment = `${name}講評: とても良い作品です`;
      });
      saveState(); render();
    }, m.name);
    const out = path.resolve(__dirname, `portalexp_member_${m.key}.xlsx`);
    const [dl] = await Promise.all([p.waitForEvent('download'), p.click('#btnXLS')]);
    await dl.saveAs(out); files.push(out);
    await p.close();
  }

  const p = await b.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error') errors.push('console.error: ' + m.text()); });
  await p.goto(AGG);
  await p.setInputFiles('#fileIn', files);
  await p.waitForTimeout(1000);

  ok((await p.locator('#btnPortalXLS').count()) === 1, '「ポータル掲載データを書き出す」ボタンがある');
  const outXlsx = path.resolve(__dirname, 'test_portal_export_out.xlsx');
  const [dl] = await Promise.all([p.waitForEvent('download'), p.click('#btnPortalXLS')]);
  await dl.saveAs(outXlsx);

  const pyOut = execSync(`python3 -c "
from openpyxl import load_workbook
wb = load_workbook('${outXlsx}', data_only=True)
print('SHEETS:', wb.sheetnames)
ws = wb['ポータル掲載データ']
rows = list(ws.iter_rows(min_row=1, values_only=True))
head = rows[0]
print('HEAD:', head)
print('ROWCOUNT:', len(rows) - 1)
tiers = [r[0] for r in rows[1:]]
print('TIERS:', tiers)
import json
print('FIRST_ROW:', json.dumps(rows[1], ensure_ascii=False, default=str))
"`).toString();
  console.log(pyOut);

  ok(pyOut.includes("SHEETS: ['ポータル掲載データ']"), 'シートが1枚（ポータル掲載データ）だけ');
  ok(pyOut.includes("'階層', '順位', '氏名・部署', '最終スコア', 'いいね数', 'HTML加点', '評価コメント', '投稿URL（作品）', '投稿URL（手順書）'"), '列見出しが想定通り');
  ok(pyOut.includes('ROWCOUNT: 10'), '受賞6件＋ノミネート4件＝10行（実際の件数はROWCOUNT参照）');
  ok(pyOut.includes("'ゴールド'"), 'ゴールドの行がある');
  ok(pyOut.includes("'シルバー'"), 'シルバーの行がある');
  ok(pyOut.includes("'ブロンズ'"), 'ブロンズの行がある');
  ok(pyOut.includes("'ノミネート'"), 'ノミネートの行がある');
  ok(!pyOut.includes('EntryCode'), '内部項目のEntryCode列が入らない');
  ok(!pyOut.includes('採点人数'), '内部項目の採点人数列が入らない');
  ok(!pyOut.includes('ルーブリック'), '内部項目のルーブリック列が入らない');
  ok(!/【[^】]+】/.test(pyOut), '評価コメントに執筆者名（【メンバー名】形式）が付かない');

  const fs = require('fs');
  fs.unlinkSync(outXlsx);

  ok(errors.length === 0, `JSエラーなし（実際: ${errors.length}件 ${errors.join(' / ')}）`);
  await b.close();
  files.forEach(f => { try { fs.unlinkSync(f); } catch (_) {} });
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
