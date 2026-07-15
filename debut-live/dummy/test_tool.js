// デビューライブ受賞選定ツールの回帰テスト（Playwright / headless Chromium）
// 実行: NODE_PATH=/opt/node22/lib/node_modules node test_tool.js
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

  await page.fill('#staffName', '田中');
  await page.fill('#targetMonth', '2026年7月');
  await page.setInputFiles('#fileMaster', path.resolve(__dirname, 'master_test.xlsx'));
  await page.waitForTimeout(1000);

  ok((await page.textContent('#hEntries')).includes('15'), '採点マスター15件が読み込まれる');
  ok((await page.textContent('#hAwards')).includes('6'), '受賞候補が自動的に6件選出される');
  ok((await page.textContent('#hGap')).includes('1'), '資料欠損1件が検出される（作品リンク未提出）');

  const topCard = await page.locator('.acard[data-code]').first().locator('.ainfo b').innerText();
  ok(topCard === 'DEBUT-2026-0013', `最終スコア1位はDEBUT-2026-0013のはず（実際: ${topCard}）`);

  // 過去の受賞者Excel（6月）を読み込み、山田太郎・佐藤花子を除外
  await page.setInputFiles('#filePast', path.resolve(__dirname, 'past_test.xlsx'));
  await page.waitForTimeout(700);
  ok((await page.textContent('#hExcl')).includes('2'), '過去受賞者2名が除外される');
  const yamadaRow = await page.locator('tbody tr', { hasText: '山田太郎' }).first().innerText();
  ok(yamadaRow.includes('受賞済み(2026年6月)'), '山田太郎の行に受賞済みバッジが付く');
  ok(!(await page.locator('tbody tr', { hasText: '山田太郎' }).first().locator('.row-rank').isEnabled()), '受賞済みの行は順位選択が無効化される');

  // 手動で順位を入れ替え：資料欠損のDEBUT-2026-0012は選べないことを確認
  const gapSelect = page.locator('tr.gap .row-rank').first();
  ok(!(await gapSelect.isEnabled()), '資料欠損の行は順位選択が無効化される');

  // 手動オーバーライド：7位相当の対象外エントリーを1位に割り当て、元1位が押し出されるか確認
  const rankSelects = page.locator('.row-rank');
  const n = await rankSelects.count();
  let movedCode = null;
  for(let i=0;i<n;i++){
    const sel = rankSelects.nth(i);
    if(await sel.isEnabled() && (await sel.inputValue()) === '0'){
      movedCode = await page.locator('tbody tr').nth(i).locator('td.ttl b').innerText();
      await sel.selectOption('1');
      break;
    }
  }
  ok(!!movedCode, '対象外だったエントリーを1位に手動で割り当てられる');
  const newTopCard = await page.locator('.acard[data-code]').first().locator('.ainfo b').innerText();
  ok(newTopCard === movedCode, `手動で1位にしたエントリー(${movedCode})が受賞候補カードの1位に反映される（実際: ${newTopCard}）`);
  const oldTopRank = await page.locator('tbody tr', { hasText: 'DEBUT-2026-0013' }).first().locator('.row-rank').inputValue();
  ok(oldTopRank === '0', '元1位だったエントリーは対象外に押し出される（順位の重複がない）');

  // 入力チェック
  await page.click('#btnCheck');
  await page.waitForTimeout(200);
  const checkText = await page.locator('#checkBody').innerText();
  ok(checkText.includes('受賞理由が未記入'), '受賞理由未記入が入力チェックで検出される');
  await page.click('#checkClose');

  // Excel書き出し
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.click('#btnXLS'),
  ]);
  const savePath = path.resolve(__dirname, 'test_output.xlsx');
  await download.saveAs(savePath);
  ok(fs.existsSync(savePath), '受賞一覧Excelが書き出される');
  fs.unlinkSync(savePath);

  ok(errors.length === 0, `JSエラーが発生していない（実際: ${errors.length}件 ${errors.join(' / ')}）`);

  await browser.close();
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
