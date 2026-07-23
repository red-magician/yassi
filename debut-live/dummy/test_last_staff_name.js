// 受賞選定ツール: 前回入力した作業者名をブラウザに覚えておき、次回開いた時に自動入力する機能の回帰テスト
const { chromium } = require('playwright');
const path = require('path');
const assert = require('assert');
function ok(c, m) { assert(c, 'FAIL: ' + m); console.log('OK:', m); }
const TOOL = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_受賞選定ツール.html');

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const ctx = await b.newContext();  // 同じブラウザコンテキスト（localStorage共有）を維持し、開き直しを再現する

  const p1 = await ctx.newPage();
  await p1.goto(TOOL);
  ok((await p1.inputValue('#staffName')) === '', '初回は作業者名が空欄');
  await p1.fill('#staffName', '城間');
  await p1.waitForTimeout(100);
  await p1.close();

  const p2 = await ctx.newPage();
  const errors = [];
  p2.on('pageerror', e => errors.push(e.message));
  await p2.goto(TOOL);
  await p2.waitForTimeout(200);
  const val = await p2.inputValue('#staffName');
  ok(val === '城間', `再度開くと前回の作業者名が自動入力される（実際: ${val}）`);

  // 別の名前に変更すればそちらが新しく記憶される
  await p2.fill('#staffName', '新田');
  await p2.waitForTimeout(100);
  await p2.close();
  const p3 = await ctx.newPage();
  await p3.goto(TOOL);
  await p3.waitForTimeout(200);
  ok((await p3.inputValue('#staffName')) === '新田', '名前を変更すれば次回はその名前が記憶される');

  ok(errors.length === 0, `JSエラーなし（実際: ${errors.length}件）`);
  await p3.close();
  await b.close();
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
