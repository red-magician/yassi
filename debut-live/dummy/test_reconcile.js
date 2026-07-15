// 受賞突合ツールの回帰テスト（Playwright / headless Chromium）
// 事前に gen_two_staff_exports.js を実行して export_田中.xlsx / export_佐藤.xlsx を用意しておくこと
// 実行: NODE_PATH=/opt/node22/lib/node_modules node test_reconcile.js
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const assert = require('assert');

function ok(cond, msg){ assert(cond, 'FAIL: ' + msg); console.log('OK:', msg); }

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', msg => { if (msg.type() === 'error') errors.push('console.error: ' + msg.text()); });

  const filePath = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_受賞突合ツール.html');
  await page.goto(filePath);

  await page.setInputFiles('#fileIn', [
    path.resolve(__dirname, 'staffA.xlsx'),
    path.resolve(__dirname, 'staffB.xlsx'),
  ]);
  await page.waitForTimeout(1000);

  ok((await page.textContent('#hFiles')).includes('2'), '2名分のExcelが読み込まれる');
  ok((await page.textContent('#hOk')).includes('5'), '6件中5件が一致と判定される');
  ok((await page.textContent('#hBad')).trim().startsWith('1'), '1件が不一致と判定される（1位）');
  ok((await page.textContent('#hScoreMismatch')).trim().startsWith('1'), 'スコア不一致が1件検出される（DEBUT-2026-0008）');

  const slot1Status = await page.locator('.slot-card').first().locator('.slot-status').innerText();
  ok(slot1Status.includes('不一致'), `1位のステータスが不一致と表示される（実際: ${slot1Status}）`);
  const cands = await page.locator('.slot-card').first().locator('.cand').count();
  ok(cands === 2, `1位の候補が2件表示される（実際: ${cands}）`);

  // 田中さんの候補（DEBUT-2026-0013）を採用する
  await page.locator('.slot-card').first().locator('input[value="DEBUT-2026-0013"]').check();
  await page.waitForTimeout(200);
  const reasonVal = await page.locator('.slot-card').first().locator('textarea[data-field="reason"]').inputValue();
  ok(reasonVal.includes('田中'), `採用した候補の受賞理由が反映される（実際: ${reasonVal}）`);

  // 2位（一致スロット）は両者とも同じ作品だが受賞理由の文言が違う→クイックフィルで差し替えられるか確認
  const slot2 = page.locator('.slot-card').nth(1);
  ok((await slot2.locator('.slot-status').innerText()).includes('一致'), '2位は一致と判定される');
  const reasonBefore = await slot2.locator('textarea[data-field="reason"]').inputValue();
  ok(reasonBefore.includes('田中') || reasonBefore.includes('佐藤'), `2位の受賞理由はどちらかの作業者の文言が初期値になる（実際: ${reasonBefore}）`);
  const otherStaff = reasonBefore.includes('田中') ? '佐藤' : '田中';
  await slot2.locator('.qf-btn', { hasText: `${otherStaff}の文言` }).first().click();
  await page.waitForTimeout(200);
  const reasonVal2 = await page.locator('.slot-card').nth(1).locator('textarea[data-field="reason"]').inputValue();
  ok(reasonVal2.includes(otherStaff), `クイックフィルでもう一方(${otherStaff})の文言に差し替えられる（実際: ${reasonVal2}）`);

  // 確定チェック→書き出し
  await page.click('#btnCheck');
  await page.waitForTimeout(200);

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.click('#btnXLS'),
  ]);
  const savePath = path.resolve(__dirname, 'test_reconcile_output.xlsx');
  await download.saveAs(savePath);
  ok(fs.existsSync(savePath), '確定版Excelが書き出される');

  const buf = fs.readFileSync(savePath);
  fs.unlinkSync(savePath);

  ok(errors.length === 0, `JSエラーが発生していない（実際: ${errors.length}件 ${errors.join(' / ')}）`);

  await browser.close();
  console.log('\nALL TESTS PASSED');
  console.log('output size:', buf.length, 'bytes');
})().catch(e => { console.error(e); process.exit(1); });
