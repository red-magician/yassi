// 実際のマスターExcelの構成（16_デビュー抽出／02_採点結果台帳／04_受賞者マスタが別シート、
// CompetitionKeyが他競技と混在、SubmitterDisplayName+Departmentが分離、一部未採点）を模した回帰テスト
// 事前に make_dummy_real_shape.py を実行して master_real_shape.xlsx を用意しておくこと
// 実行: NODE_PATH=/opt/node22/lib/node_modules node test_real_shape.js
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
  await page.setInputFiles('#fileMaster', path.resolve(__dirname, 'master_real_shape.xlsx'));
  await page.waitForTimeout(1200);

  // デビュー投稿15件のうち1件は非公開（IsHidden）なので14件のみ（他競技混入1件も除外される）
  ok((await page.textContent('#hEntries')).includes('14'), '他競技混入・非公開エントリーを除いた14件が読み込まれる');
  ok((await page.textContent('#hUnscored')).trim().startsWith('3'), '未採点3件が検出される（14件中11件のみAI採点済み）');
  ok((await page.textContent('#targetMonth')).length >= 0, 'targetMonth要素が存在する');
  const monthVal = await page.inputValue('#targetMonth');
  ok(monthVal === 'debut-cool2', `PeriodKeyから対象月が自動入力される（実際: ${monthVal}）`);

  // 04_受賞者マスタの内蔵除外（Yamada, Taro / SubmitterEntraIdでの突合）
  ok((await page.textContent('#hExcl')).trim().startsWith('1'), '04_受賞者マスタから1名が除外される');
  const yamadaRow = await page.locator('tbody tr', { hasText: 'Yamada, Taro' }).first().innerText();
  ok(yamadaRow.includes('受賞済み'), `Yamadaさんの行に受賞済みバッジが付く（実際: ${yamadaRow.replace(/\n/g,' | ')}）`);
  const noteText = await page.locator('#masterExclNote').innerText();
  ok(noteText.includes('04_受賞者マスタ'), '04_受賞者マスタから反映した旨のバナーが表示される');

  // HTML加点がURL拡張子から推定されている（.mdの1件は+0、手順書ありの1件は+10）
  const mdRow = await page.locator('tbody tr', { hasText: 'DEBUT-2026-000005' }).first().innerText();
  ok(mdRow.includes('加点なし'), `.md提出の作品はHTML加点なし（実際: ${mdRow.replace(/\n/g,' | ')}）`);

  // 受賞候補は未採点・非公開・他競技・受賞済みのいずれでもない
  const winBadges = await page.locator('.badge.win').count();
  ok(winBadges === 6, `受賞候補6件が自動選出される（実際: ${winBadges}）`);
  const excludedWin = await page.locator('tbody tr:has-text("受賞済み") .badge.win').count();
  ok(excludedWin === 0, '受賞済みの応募者は受賞候補に選ばれない');
  const unscoredWin = await page.locator('tbody tr:has-text("未採点") .badge.win').count();
  ok(unscoredWin === 0, '未採点の作品は受賞候補に選ばれない');

  ok(errors.length === 0, `JSエラーが発生していない（実際: ${errors.length}件 ${errors.join(' / ')}）`);

  await browser.close();
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
