// 受賞選定ツールに「集計ツールの結果Excel」取り込み機能を追加した回帰テスト。
// 集計ツールが書き出した「受賞・ノミネート一覧」シートを読み込ませ、
// 総合順位(上位6件)が受賞候補に反映され、講評コメントも入ることを確認する。
const { chromium } = require('playwright');
const path = require('path');
const assert = require('assert');
function ok(c, m) { assert(c, 'FAIL: ' + m); console.log('OK:', m); }

const TOOL = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_受賞選定ツール.html');
const AGG_TOOL = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_集計ツール_3人平均.html');
const MASTER = path.resolve(__dirname, 'master_test.xlsx');

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });

  // --- 3人分のエクスポートを生成して集計ツールに読み込み、結果Excelを作る ---
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
        notes[e.code].comment = `${name}さんのコメント: よくできています`;
      });
      saveState(); render();
    }, m.name);
    const out = path.resolve(__dirname, `agg_member_${m.key}.xlsx`);
    const [dl] = await Promise.all([p.waitForEvent('download'), p.click('#btnXLS')]);
    await dl.saveAs(out); files.push(out);
    await p.close();
  }

  const aggPage = await b.newPage();
  await aggPage.goto(AGG_TOOL);
  await aggPage.setInputFiles('#fileIn', files);
  await aggPage.waitForTimeout(1000);
  const [dl2] = await Promise.all([aggPage.waitForEvent('download'), aggPage.click('#btnXLS')]);
  const aggOut = path.resolve(__dirname, 'agg_result_for_import.xlsx');
  await dl2.saveAs(aggOut);
  await aggPage.close();

  // --- 受賞選定ツールに、まず採点マスターを読み込んでから集計結果Excelを取り込む ---
  const p = await b.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error') errors.push('console.error: ' + m.text()); });
  await p.goto(TOOL);
  await p.fill('#staffName', '事務局');
  await p.fill('#targetMonth', '2026年7月');
  await p.setInputFiles('#fileMaster', MASTER);
  await p.waitForTimeout(800);

  // 先に取り込みを試して「先に読み込んでください」エラーにならないことを確認済みなので、ここから集計結果を読み込む
  await p.setInputFiles('#fileAgg', aggOut);
  await p.waitForTimeout(800);

  const info = await p.evaluate(() => {
    const winCodes = Object.keys(ranks);
    return {
      winCount: winCodes.length,
      sampleComment: winCodes.length ? (notes[winCodes[0]] || {}).comment : '',
      pinnedCount: Object.keys(pinned).length,
    };
  });
  ok(info.winCount === 6, `受賞候補6件が反映される（実際: ${info.winCount}）`);
  ok(info.pinnedCount === 6, `総合順位が6件とも手動固定として反映される（実際: ${info.pinnedCount}）`);
  ok(!!info.sampleComment, `講評コメントが反映される（実際: ${JSON.stringify(info.sampleComment).slice(0, 40)}）`);

  ok(errors.length === 0, `JSエラーなし（実際: ${errors.length}件 ${errors.join(' / ')}）`);
  await b.close();
  files.forEach(f => { try { require('fs').unlinkSync(f); } catch (_) {} });
  try { require('fs').unlinkSync(aggOut); } catch (_) {}
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
