// ポータルの「対象者」シート形式（列名が SubmitterDisplayName ではなく 投稿者／所属／LikeCount／
// 投稿者LikesGiven件数（全競技）で、シート名も「デビュー抽出」を含まない）を読み込めるかの回帰テスト。
// 事前に make_dummy_target_sheet.py を実行して master_target_sheet.xlsx を用意しておくこと
// 実行: NODE_PATH=/opt/node22/lib/node_modules node test_target_sheet.js
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
  await page.setInputFiles('#fileMaster', path.resolve(__dirname, 'master_target_sheet.xlsx'));
  await page.waitForTimeout(1200);

  // 10件中、他競技(solo)・非公開(IsHidden)・下書き(Status≠Published)の3件が除外され7件
  ok((await page.textContent('#hEntries')).includes('7'), '「対象者」シートの7件（除外3件を除く）が読み込まれる');

  // 行数の多い「全件版」シートではなく「対象者」シートが優先される（全件版だけに入る1名が出ない）
  const extraCount = await page.locator('tbody tr', { hasText: 'Extra, Person' }).count();
  ok(extraCount === 0, '行数の多い全件版シートではなく「対象者」シートが優先して読み込まれる');

  const monthVal = await page.inputValue('#targetMonth');
  ok(monthVal === 'debut-cool3', `PeriodKeyから対象月が自動入力される（実際: ${monthVal}）`);

  // 投稿者・所属（新形式の列名）が正しく分割・結合される
  const yamadaRow = await page.locator('tbody tr', { hasText: 'Yamada, Taro' }).first().innerText();
  ok(yamadaRow.includes('AIX本部'), `投稿者名・所属（新列名）が読み取れる（実際: ${yamadaRow.replace(/\n/g,' | ')}）`);

  // LikeCount／投稿者LikesGiven件数（全競技）から、いいね（もらう/押す）が読み取れる
  const row1 = await page.evaluate(() => {
    const e = ENTRIES.find(x => x.code === 'DEBUT-2026-000001');
    return e && { likesRaw: e.likesRaw, likesGivenRaw: e.likesGivenRaw, gap: e.gap, fmtWork: e.fmtWork };
  });
  ok(row1 && row1.likesRaw === 12 && row1.likesGivenRaw === 40, `LikeCount(12)/投稿者LikesGiven件数（40）が読み取れる（実際: ${JSON.stringify(row1)}）`);

  // 作品リンク未提出の1件（DEBUT-2026-000007）は資料欠損として検出される
  const gapRow = await page.evaluate(() => {
    const e = ENTRIES.find(x => x.code === 'DEBUT-2026-000007');
    return e && e.gap;
  });
  ok(gapRow === true, '作品リンク未提出のエントリーが資料欠損として検出される');

  // Markdown提出の1件（DEBUT-2026-000006）はHTML加点なし
  const mdRow = await page.locator('tbody tr', { hasText: 'DEBUT-2026-000006' }).first().innerText();
  ok(mdRow.includes('加点なし'), `.md提出はHTML加点なし（実際: ${mdRow.replace(/\n/g,' | ')}）`);

  ok(errors.length === 0, `JSエラーが発生していない（実際: ${errors.length}件 ${errors.join(' / ')}）`);

  await browser.close();
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
