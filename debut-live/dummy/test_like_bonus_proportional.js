// いいね加点の「相対配点」方式（対象者全員の中で最も多い人を満点(もらう20点/押す40点)とし、
// 他の人はその人との比率で点数がつく。個人ごとの絶対的な上限は無い）の回帰テスト。
// 事前に make_dummy_like_bonus.py を実行して like_bonus_test.xlsx を用意しておくこと
// 実行: NODE_PATH=/opt/node22/lib/node_modules node test_like_bonus_proportional.js
const { chromium } = require('playwright');
const path = require('path');
const assert = require('assert');

function ok(cond, msg){ assert(cond, 'FAIL: ' + msg); console.log('OK:', msg); }
function close(a, b, eps=0.05){ return Math.abs(a-b) < eps; }

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', msg => { if (msg.type() === 'error') errors.push('console.error: ' + msg.text()); });

  const filePath = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_受賞選定ツール.html');
  await page.goto(filePath);
  await page.setInputFiles('#fileMaster', path.resolve(__dirname, 'like_bonus_test.xlsx'));
  await page.waitForTimeout(1000);

  const bonuses = await page.evaluate(() => Object.fromEntries(
    ENTRIES.map(e => [e.code, { recv: e.recvBonus, give: e.giveBonus, total: e.likeBonus, likesRaw: e.likesRaw, likesGivenRaw: e.likesGivenRaw }])
  ));
  console.log(JSON.stringify(bonuses, null, 2));

  const a = bonuses['DEBUT-2026-0001'], b = bonuses['DEBUT-2026-0002'], c = bonuses['DEBUT-2026-0003'], d = bonuses['DEBUT-2026-0004'];

  // A社員：もらう最多(100件) → 満点20。押すは0件 → 0
  ok(close(a.recv, 20), `もらう最多者は満点20になる（個人ごとの上限ではなく対象者内の最多値が基準・実際: ${a.recv}）`);
  ok(close(a.give, 0), `押す0件は加点0（実際: ${a.give}）`);

  // B社員：もらう50件は最多(100件)の半分 → 10。押す最多(200件) → 満点40
  ok(close(b.recv, 10), `もらう50件＝最多100件の半分なので10点になる（比例配点・実際: ${b.recv}）`);
  ok(close(b.give, 40), `押す最多者は満点40になる（実際: ${b.give}）`);

  // C社員：もらう25件は最多の1/4 → 5。押す100件は最多200件の半分 → 20
  ok(close(c.recv, 5), `もらう25件＝最多100件の1/4なので5点になる（実際: ${c.recv}）`);
  ok(close(c.give, 20), `押す100件＝最多200件の半分なので20点になる（実際: ${c.give}）`);

  // D社員：どちらも0件 → 加点0（ゼロ除算にならないこと）
  ok(close(d.recv, 0) && close(d.give, 0), `いいね0件は加点0になる（実際: ${JSON.stringify(d)}）`);

  // 従来の「個人ごとの上限」（もらう+20/押す+40）を超える生の値でも、
  // 相対配点である以上、最多者以外が満点を超えることはない
  ok(a.recv <= 20 && b.give <= 40 && c.give <= 40, '最多者以外が満点を超えることはない');

  ok(errors.length === 0, `JSエラーが発生していない（実際: ${errors.length}件 ${errors.join(' / ')}）`);

  await browser.close();
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
