// 内部スタッフが画面でルーブリック点数を直接入力 → 最終スコア・順位が自動計算 → エクスポートに反映される、を検証
// 事前に make_dummy_real_shape.py（未採点エントリーを含むダミー）を実行しておくこと
// 実行: NODE_PATH=/opt/node22/lib/node_modules node test_manual_scoring.js
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

  const filePath = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_受賞選定ツール.html');
  await page.goto(filePath);
  await page.fill('#staffName', '検証');
  await page.setInputFiles('#fileMaster', path.resolve(__dirname, 'master_real_shape.xlsx'));
  await page.waitForTimeout(1000);

  const unscoredBefore = Number((await page.textContent('#hUnscored')).trim().match(/\d+/)[0]);
  ok(unscoredBefore >= 1, `最初に未採点のエントリーがある（${unscoredBefore}件）`);

  // 未採点の行のコードを控える（採点すると .unscored クラスが外れるので、以降はコードで行を特定する）
  const code = await page.locator('tbody tr.unscored').first().locator('td.ttl b').innerText();
  console.log('採点対象（未採点）:', code);
  const rowOf = () => page.locator('tbody tr', { hasText: code }).first();
  const scoreInp = (i) => rowOf().locator('.score-inp').nth(i);

  // 観点①〜④に 10/10/10/10 を入力（満点 → ルーブリック100）
  for (let i = 0; i < 4; i++) {
    await scoreInp(i).fill('10');
    await scoreInp(i).dispatchEvent('change');
    await page.waitForTimeout(80);
  }
  await page.waitForTimeout(300);

  // その行のルーブリックが100になっている
  const rub = await page.locator(`#rub-${code} .sc`).innerText();
  ok(rub === '100', `入力後のルーブリックが100になる（実際: ${rub}）`);
  const unscoredAfter = Number((await page.textContent('#hUnscored')).trim().match(/\d+/)[0]);
  ok(unscoredAfter === unscoredBefore - 1, `未採点件数が1件減る（${unscoredBefore}→${unscoredAfter}）`);

  // 満点なので受賞候補1位に入っているはず（いいね加点・HTML加点次第だが最上位クラス）
  const inWin = await page.locator('.acard[data-code]').evaluateAll((cards, c) =>
    cards.some(el => el.getAttribute('data-code') === c), code);
  ok(inWin, `満点採点したエントリーが受賞候補カードに入る`);

  // 点数を全消去すると未採点に戻る
  for (let i = 0; i < 4; i++) {
    await scoreInp(i).fill('');
    await scoreInp(i).dispatchEvent('change');
    await page.waitForTimeout(80);
  }
  await page.waitForTimeout(300);
  const unscoredReset = Number((await page.textContent('#hUnscored')).trim().match(/\d+/)[0]);
  ok(unscoredReset === unscoredBefore, `点数を消すと未採点に戻る（${unscoredReset}）`);

  // 改めて 8/5/8/2 を入力してエクスポートに反映されるか確認
  const vals = ['8','5','8','2'];
  for (let i = 0; i < 4; i++) {
    await scoreInp(i).fill(vals[i]);
    await scoreInp(i).dispatchEvent('change');
    await page.waitForTimeout(80);
  }
  await page.waitForTimeout(300);
  // 8/5/8/2 → (8+5+8+2)/10*25 = 23/... 実際は各 v/10*25 の和 = (8+5+8+2)/10*25 = 57.5
  const rub2 = await page.locator(`#rub-${code} .sc`).innerText();
  ok(rub2 === '57.5', `8/5/8/2 のルーブリックが57.5になる（実際: ${rub2}）`);

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.click('#btnXLS'),
  ]);
  const savePath = path.resolve(__dirname, 'test_manual_output.xlsx');
  await download.saveAs(savePath);
  ok(fs.existsSync(savePath), 'Excelが書き出される（中身の観点スコアは verify_manual_export.py で確認）');
  console.log('SAVED_CODE=' + code);

  ok(errors.length === 0, `JSエラーが発生していない（実際: ${errors.length}件 ${errors.join(' / ')}）`);

  await browser.close();
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
