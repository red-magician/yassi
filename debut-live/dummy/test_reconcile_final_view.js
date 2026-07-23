// 集計ツール（3人平均）の新機能の回帰テスト:
// 1. 「採点比較」/「最終結果」の2画面切替
// 2. 受賞理由が、採用元メンバーの講評コメントを自動で流用すること
// 3. 書き出しExcelに受賞理由列が追加されていること
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
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
    const out = path.resolve(__dirname, `finalview_member_${m.key}.xlsx`);
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

  // デフォルトは「採点比較」タブ
  ok((await p.locator('.view-tab.on').textContent()) === '採点比較', 'デフォルトは採点比較タブ');
  ok((await p.locator('h2:has-text("採点比較")').count()) === 1, '採点比較の表が表示される');

  // 「最終結果」タブへ切替
  await p.click('.view-tab[data-view="final"]');
  await p.waitForTimeout(200);
  ok((await p.locator('h2:has-text("最終結果")').count()) === 1, '最終結果の表に切り替わる');
  ok((await p.locator('#out tbody tr').count()) === 10, '最終結果には上位10件だけが表示される');

  // コメント採用元を「田中」にして、受賞理由に田中の講評がそのまま入ることを確認
  await p.selectOption('#commentMemberSel', { label: '田中のみ' });
  await p.waitForTimeout(200);
  const firstRowText = await p.locator('#out tbody tr').first().innerText();
  ok(firstRowText.includes('田中講評'), `受賞理由に採用元メンバーの講評コメントがそのまま入る（実際: ${firstRowText.replace(/\n/g, ' | ').slice(0, 200)}）`);

  // 書き出しExcelに受賞理由列があることを確認（python/openpyxlで検証）
  const [dl] = await Promise.all([p.waitForEvent('download'), p.click('#btnXLS')]);
  const outXlsx = path.resolve(__dirname, 'test_finalview_out.xlsx');
  await dl.saveAs(outXlsx);
  const { execSync } = require('child_process');
  const pyOut = execSync(`python3 -c "
from openpyxl import load_workbook
wb = load_workbook('${outXlsx}', data_only=True)
ws = wb['受賞・ノミネート一覧']
rows = list(ws.iter_rows(min_row=1, max_row=2, values_only=True))
head = rows[0]
print('HEAD:', head)
i = [j for j,h in enumerate(head) if h and str(h).startswith('受賞理由')]
print('REASON_COL_FOUND:', bool(i))
if i:
    print('REASON_VAL:', rows[1][i[0]])
"`).toString();
  console.log(pyOut);
  ok(pyOut.includes('REASON_COL_FOUND: True'), '書き出しExcelに受賞理由列がある');
  ok(pyOut.includes('田中講評'), '書き出しExcelの受賞理由に採用元メンバーの講評が入っている');
  fs.unlinkSync(outXlsx);

  ok(errors.length === 0, `JSエラーなし（実際: ${errors.length}件 ${errors.join(' / ')}）`);
  await b.close();
  files.forEach(f => { try { fs.unlinkSync(f); } catch (_) {} });
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
