// 「過去の受賞者Excelを追加」に、ポータルの総合ランキング一覧形式（列名が「順位」ではなく
// 「ランキング」で、「受賞フラグ」列がありノミネートのみ＝未受賞の行も混在する）を読み込ませた
// 場合の回帰テスト。実際に受賞した行だけが除外リストに入り、ノミネートのみの行は入らないことを確認する。
// 事前に make_dummy.py と make_dummy_ranking_award.py を実行しておくこと
// 実行: NODE_PATH=/opt/node22/lib/node_modules node test_ranking_award_import.js
const { chromium } = require('playwright');
const path = require('path');
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
  await page.setInputFiles('#fileMaster', path.resolve(__dirname, 'master_test.xlsx'));
  await page.waitForTimeout(1000);
  await page.setInputFiles('#filePast', path.resolve(__dirname, 'ranking_award_test.xlsx'));
  await page.waitForTimeout(1000);

  const toast = await page.locator('#toast').innerText();
  ok(toast.includes('2名'), `「ランキング」形式の受賞一覧が読み込め、受賞フラグ='受賞'の2名だけが除外対象になる（実際: ${toast}）`);

  const pastPanel = await page.locator('#pastFiles').innerText();
  ok(pastPanel.includes('2名除外'), `過去ファイルパネルにも2名除外と表示される（実際: ${pastPanel.replace(/\n/g,' | ')}）`);

  // ノミネートのみ（未受賞）の Suzuki, Ichiro / Takahashi, Misaki は除外リストに入っていないこと
  const excludedNames = await page.evaluate(() => PAST_FILES.flatMap(p => [...p.names]));
  ok(excludedNames.includes('Yamada, Taro') && excludedNames.includes('Sato, Hanako'),
    `実際に受賞した2名（Yamada, Taro / Sato, Hanako）が除外リストに入る（実際: ${JSON.stringify(excludedNames)}）`);
  ok(!excludedNames.includes('Suzuki, Ichiro') && !excludedNames.includes('Takahashi, Misaki'),
    `ノミネートのみ（未受賞）の2名は除外リストに入らない（実際: ${JSON.stringify(excludedNames)}）`);

  ok(errors.length === 0, `JSエラーが発生していない（実際: ${errors.length}件 ${errors.join(' / ')}）`);

  await browser.close();
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
