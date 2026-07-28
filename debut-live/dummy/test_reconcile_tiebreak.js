// 集計ツール（3人平均）: 同点時のタイブレーク順序（①平均ルーブリック→②いいね数→③EntryCode）の回帰テスト
// （かつてEntryCodeのアルファベット順だけで決まってしまっていたバグの再発防止）
const { chromium } = require('playwright');
const path = require('path');
const assert = require('assert');
function ok(c, m) { assert(c, 'FAIL: ' + m); console.log('OK:', m); }

const AGG = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_集計ツール_3人平均.html');

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const p = await b.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(AGG);

  // ダミーの3人分のFILESを直接注入して2パターンのタイを作る：
  // ① ルーブリックも同点 → いいね数が多い方が勝つ（ZZZ-002 vs AAA-001。EntryCodeのアルファベット順なら逆転してしまうはずの状況）
  // ② ルーブリックが違う → いいねが多くてもルーブリックが高い方が優先される（P1がQ1に勝つ）
  const result = await p.evaluate(() => {
    FILES = [
      { name: 'a.xlsx', memberName: '田中', month: '2026年7月', entries: {
        'AAA-001': { who: 'Aさん', finalScore: 90, rubricTotal: 40, likeBonus: 40, htmlBonus: 10, likesRaw: 20, likesGivenRaw: 5, comment: '' },
        'ZZZ-002': { who: 'Zさん', finalScore: 90, rubricTotal: 40, likeBonus: 40, htmlBonus: 10, likesRaw: 80, likesGivenRaw: 5, comment: '' },
        'MMM-003': { who: 'Mさん', finalScore: 70, rubricTotal: 30, likeBonus: 30, htmlBonus: 10, likesRaw: 10, likesGivenRaw: 5, comment: '' },
        'P1-RUBRIC-HIGH': { who: 'Pさん（ルーブリック高・いいね少）', finalScore: 55, rubricTotal: 45, likeBonus: 0, likesRaw: 20, likesGivenRaw: 0, comment: '' },
        'Q1-LIKES-HIGH':   { who: 'Qさん（ルーブリック低・いいね多）', finalScore: 55, rubricTotal: 15, likeBonus: 30, likesRaw: 80, likesGivenRaw: 0, comment: '' },
      }},
    ];
    pinned = {}; reasons = {};
    render();
    const agg = aggregate();
    const { ranks } = computeRanks(agg);
    return { ranks };
  });
  console.log(result.ranks);
  ok(result.ranks['ZZZ-002'] === 1, `①ルーブリック同点時：いいね数が多いZZZ-002が1位になる（実際: ${result.ranks['ZZZ-002']}位）`);
  ok(result.ranks['AAA-001'] === 2, `①ルーブリック同点時：いいね数が少ないAAA-001は2位になる（実際: ${result.ranks['AAA-001']}位）`);
  ok(result.ranks['MMM-003'] === 3, `スコア70点のMMM-003は3位（実際: ${result.ranks['MMM-003']}位）`);
  ok(result.ranks['P1-RUBRIC-HIGH'] < result.ranks['Q1-LIKES-HIGH'],
    `②最終スコア同点時：いいねが少なくてもルーブリックが高いPさんが優先される（実際: P=${result.ranks['P1-RUBRIC-HIGH']}位 / Q=${result.ranks['Q1-LIKES-HIGH']}位）`);

  ok(errors.length === 0, `JSエラーなし（実際: ${errors.length}件 ${errors.join(' / ')}）`);
  await b.close();
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
