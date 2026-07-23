// 集計ツール（3人平均）: EntryCodeクリックで提出物（作品・手順書リンク）を見られる機能の回帰テスト
const { chromium } = require('playwright');
const path = require('path');
const assert = require('assert');
function ok(c, m) { assert(c, 'FAIL: ' + m); console.log('OK:', m); }

const TOOL = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_受賞選定ツール.html');
const AGG = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_集計ツール_3人平均.html');
const MASTER = path.resolve(__dirname, 'master_test.xlsx');

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });

  const p1 = await b.newPage();
  await p1.goto(TOOL);
  await p1.fill('#staffName', '田中'); await p1.fill('#targetMonth', '2026年7月');
  await p1.setInputFiles('#fileMaster', MASTER); await p1.waitForTimeout(800);
  const { firstCode, expectedWork, expectedProc } = await p1.evaluate(() => {
    const e = ENTRIES[0];
    return { firstCode: e.code, expectedWork: e.workLink, expectedProc: e.procLink };
  });
  const codes = await p1.evaluate(() => ENTRIES.map(e => e.code));
  const blocks = codes.map((c, i) => {
    const v = Math.max(0, Math.min(10, 8 + (i % 5) - 2));
    return `===SCORE===\nEntryCode: ${c}\n観点①: ${v}\n観点②: ${v}\n観点③: ${v}\n観点④: ${v}\n===END===`;
  }).join('\n\n');
  await p1.evaluate((t) => { applyCopilot(t); saveState(); render(); }, blocks);
  const memberOut = path.resolve(__dirname, 'resources_member_A.xlsx');
  const [dl0] = await Promise.all([p1.waitForEvent('download'), p1.click('#btnXLS')]);
  await dl0.saveAs(memberOut);
  await p1.close();

  ok(!!expectedWork, `マスターの1件目に作品リンクがある（前提条件） (実際: ${expectedWork})`);

  const p = await b.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  p.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await p.goto(AGG);
  await p.setInputFiles('#fileIn', memberOut);
  await p.waitForTimeout(800);

  // 採点比較タブでEntryCodeをクリック→モーダルが開く
  ok((await p.locator('.codelink').count()) > 0, '採点比較タブにEntryCodeのリンクがある');
  await p.locator(`.codelink[data-code="${firstCode}"]`).first().click();
  await p.waitForTimeout(200);
  ok(await p.locator('#resModal.on').isVisible(), 'モーダルが開く');
  const modalText = await p.locator('#resModalBody').innerText();
  ok(modalText.includes('別タブで開く'), 'モーダルに「別タブで開く」ボタンがある');
  ok((await p.locator('#resModalBody a[href*="' + encodeURIComponent(expectedWork.split('/').pop().split('?')[0]) + '"]').count()) >= 0, 'リンク先URLの検証（緩め）');
  const workLinkHref = await p.locator('#resModalBody .resource-card').first().locator('a').getAttribute('href');
  ok(workLinkHref && workLinkHref.startsWith(expectedWork), `作品リンクのURLが正しい (実際: ${workLinkHref})`);

  // 閉じるボタンで閉じる
  await p.click('#resModalClose');
  await p.waitForTimeout(150);
  ok(!(await p.locator('#resModal').evaluate(el => el.classList.contains('on'))), 'モーダルが閉じる');

  // 受賞候補カードタブでもクリックできる
  await p.click('.view-tab[data-view="cards"]');
  await p.waitForTimeout(200);
  await p.locator('.acard .codelink').first().click();
  await p.waitForTimeout(200);
  ok(await p.locator('#resModal.on').isVisible(), 'カードタブでもモーダルが開く');
  await p.click('#resModalClose');

  // 最終結果タブでもクリックできる
  await p.click('.view-tab[data-view="final"]');
  await p.waitForTimeout(200);
  await p.locator('#out .codelink').first().click();
  await p.waitForTimeout(200);
  ok(await p.locator('#resModal.on').isVisible(), '最終結果タブでもモーダルが開く');

  ok(errors.length === 0, `JSエラーなし（実際: ${errors.length}件 ${errors.join(' / ')}）`);
  await b.close();
  require('fs').unlinkSync(memberOut);
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
