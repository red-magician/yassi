// 集計ツール（3人平均）: 「ポータル表示」タブの回帰テスト
// ポータル班から共有された実際のデザイン（ゴールド/シルバー/ブロンズのメダル階層カード＋ノミネート一覧）に
// 構成を合わせている。配色は本ツール既存の紺・ゴールドのまま。内部用語（ルーブリック・観点・採点人数など）は出さない
const { chromium } = require('playwright');
const path = require('path');
const assert = require('assert');
function ok(c, m) { assert(c, 'FAIL: ' + m); console.log('OK:', m); }

const TOOL = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_受賞選定ツール.html');
const AGG = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_集計ツール_3人平均.html');
const MASTER = path.resolve(__dirname, 'master_test.xlsx');

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });

  const members = [{ name: '田中', key: 'A', base: 8 }, { name: '佐藤', key: 'B', base: 6 }, { name: '鈴木', key: 'C', base: 10 }];
  const files = [];
  for (const m of members) {
    const p = await b.newPage();
    await p.goto(TOOL);
    await p.fill('#staffName', m.name); await p.fill('#targetMonth', '2026年7月');
    await p.setInputFiles('#fileMaster', MASTER); await p.waitForTimeout(800);
    const codes = await p.evaluate(() => ENTRIES.map(e => e.code));
    const blocks = codes.map((c, i) => {
      const v = Math.max(0, Math.min(10, m.base + (i % 5) - 2));
      return `===SCORE===\nEntryCode: ${c}\n観点①: ${v}\n観点②: ${v}\n観点③: ${v}\n観点④: ${v}\n===END===`;
    }).join('\n\n');
    await p.evaluate((t) => { applyCopilot(t); saveState(); render(); }, blocks);
    await p.evaluate((name) => {
      ENTRIES.forEach(e => {
        notes[e.code] = notes[e.code] || { reason: '', comment: '' };
        notes[e.code].comment = `${name}講評: とても良い作品です`;
      });
      saveState(); render();
    }, m.name);
    const out = path.resolve(__dirname, `portal_member_${m.key}.xlsx`);
    const [dl] = await Promise.all([p.waitForEvent('download'), p.click('#btnXLS')]);
    await dl.saveAs(out); files.push(out);
    await p.close();
  }

  const p = await b.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error') errors.push('console.error: ' + m.text()); });
  await p.goto(AGG);
  await p.setInputFiles('#fileIn', files);
  await p.waitForTimeout(1000);

  ok((await p.locator('.view-tab').count()) === 4, 'ツールバーに4つのタブがある（採点比較/受賞候補カード/最終結果/ポータル表示）');
  await p.click('.view-tab[data-view="portal"]');
  await p.waitForTimeout(300);
  ok((await p.locator('.view-tab.on').textContent()) === 'ポータル表示', 'ポータル表示タブがアクティブになる');

  // 案内文（公式の配点構成：書く40／学ぶ40／響く20／＋α10＝110点）
  const announceText = await p.locator('.portal-announce').innerText();
  ok(announceText.includes('書く（40点）'), '案内文に「書く（40点）」の表記がある');
  ok(announceText.includes('学ぶ（40点）'), '案内文に「学ぶ（40点）」の表記がある');
  ok(announceText.includes('響く（20点）'), '案内文に「響く（20点）」の表記がある');
  ok(announceText.includes('Cowork'), '案内文に＋α（Cowork経由の自動加点）の説明がある');
  ok(announceText.includes('110点'), '案内文に満点110点の記載がある');
  ok(!announceText.includes('ルーブリック'), '案内文に内部用語「ルーブリック」が出ない');
  ok(announceText.includes('1件につき1点、最大40点までスコアに反映されます') && announceText.includes('1件につき1点、最大20点までスコアに反映されます'),
    '案内文の学ぶ／響く説明が「1件につき1点、最大◯点まで」という誤解のない前向きな言い回しになっている');
  ok(!announceText.includes('頭打ち'), '案内文にネガティブな言い回し「頭打ち」が使われていない');
  ok(!announceText.includes('までは、') && !announceText.includes('までは、押した数がそのまま得点に積み上がります'),
    '案内文が「〜までは」という、上限超過後も何かが続くかのように読める言い回しになっていない');

  // メダル階層（ゴールド1名／シルバー2名／ブロンズ3名 ＝ 受賞6件）
  ok((await p.locator('.pt-tier.gold .pt-card').count()) === 1, 'ゴールドアワードが1名（実際:' + (await p.locator('.pt-tier.gold .pt-card').count()) + '）');
  ok((await p.locator('.pt-tier.silver .pt-card').count()) === 2, 'シルバーアワードが2名');
  ok((await p.locator('.pt-tier.bronze .pt-card').count()) === 3, 'ブロンズアワードが3名');
  ok((await p.locator('.pt-card').count()) === 6, '受賞カードは合計6枚');

  const goldCardText = await p.locator('.pt-tier.gold .pt-card').innerText();
  ok(!/採点人数/.test(goldCardText), 'カードに採点人数が出ない');
  ok(!/DEBUT-2026/.test(goldCardText), 'カードにEntryCodeが出ない（応募者名で表示）');
  ok(/書く/.test(goldCardText) && /学ぶ（押したいいね）/.test(goldCardText) && /響く（もらったいいね）/.test(goldCardText) && /＋α（Cowork）/.test(goldCardText),
    'カードに書く／学ぶ（押したいいね）／響く（もらったいいね）／＋α（Cowork）の4スタッツが出る');
  ok(/\/ 110点/.test(goldCardText), 'カードの最終スコアが110点満点表記になっている');

  // 学ぶ・響くは「もらったいいねの総数」ではなく、上限で頭打ちした得点そのものを表示する（ポータル班からの要望）
  ok(/\/40点/.test(goldCardText) && /\/20点/.test(goldCardText), 'カードの学ぶ／響くは「/40点」「/20点」の得点表示になっている（総数表示ではない）');
  const goldStats = await p.evaluate(() => {
    const el = document.querySelector('.pt-tier.gold .pt-card');
    const d2 = el.querySelector('.pt-stat.d2 .v').childNodes[0].textContent.trim();
    const d3 = el.querySelector('.pt-stat.d3 .v').childNodes[0].textContent.trim();
    const code = el.querySelector('.codelink').dataset.code;
    const raw = aggregate().find(e => e.code === code);
    return { d2, d3, given: raw.likesGivenRaw, received: raw.likesRaw };
  });
  ok(Number(goldStats.d2) === Math.min(goldStats.given, 40), `学ぶの表示値(${goldStats.d2})が押したいいねの得点（上限40で頭打ち、実数${goldStats.given}）と一致する`);
  ok(Number(goldStats.d3) === Math.min(goldStats.received, 20), `響くの表示値(${goldStats.d3})がもらったいいねの得点（上限20で頭打ち、実数${goldStats.received}）と一致する`);

  // ポータル班レビュー対応：得点（メイン）に加え、生のいいね数もサブ表示で併記する
  ok(new RegExp(`いいね ${goldStats.given}件`).test(goldCardText), `学ぶのカードに生のいいね数（押した${goldStats.given}件）がサブ表示される`);
  ok(new RegExp(`いいね ${goldStats.received}件`).test(goldCardText), `響くのカードに生のいいね数（もらった${goldStats.received}件）がサブ表示される`);
  ok(/田中講評|佐藤講評|鈴木講評/.test(goldCardText), '評価コメント本文は表示される');
  const commentLine = goldCardText.split('\n').find(l => /講評/.test(l)) || '';
  ok(!/^【/.test(commentLine), '評価コメントに執筆者名（【メンバー名】形式）が付かない');
  ok(/投稿を見る/.test(goldCardText), '「投稿を見る」リンクがある');

  // リンククリックでモーダルが開く
  await p.locator('.pt-tier.gold .codelink').first().click();
  await p.waitForTimeout(300);
  ok(await p.locator('#resModal.on').isVisible(), 'ポータル表示のカードからも資料モーダルが開く');
  await p.click('#resModalClose');
  await p.waitForTimeout(200);

  // ノミネート一覧（上位10件のうち受賞6件を除く4件）
  const nomCount = await p.locator('.pt-nominee-item').count();
  ok(nomCount === 4, `ノミネート一覧が4件（実際:${nomCount}）`);
  const nomText = await p.locator('.pt-nominees').innerText();
  ok(!/採点人数/.test(nomText), 'ノミネート一覧にも採点人数が出ない');
  ok(!/DEBUT-2026/.test(nomText), 'ノミネート一覧にもEntryCodeが出ない');

  ok(errors.length === 0, `JSエラーなし（実際: ${errors.length}件 ${errors.join(' / ')}）`);
  await b.close();
  const fs = require('fs');
  files.forEach(f => { try { fs.unlinkSync(f); } catch (_) {} });
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
