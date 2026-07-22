// デビューライブ 集計ツール（3人平均）の回帰テスト。
// 受賞選定ツールで3人分のエクスポートを生成 → 集計ツールで平均・順位付け・ノミネート/受賞・手動固定・書き出しを検証。
// 実行: NODE_PATH=/opt/node22/lib/node_modules node test_reconcile.js
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
const assert = require('assert');
function ok(c,m){ assert(c,'FAIL: '+m); console.log('OK:', m); }

const SEL = 'file://'+path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_受賞選定ツール.html');
const AGG = 'file://'+path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_集計ツール_3人平均.html');
const MASTER = path.resolve(__dirname, 'master_test.xlsx');

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });

  // --- 3人分のエクスポートを生成（メンバーごとに base をずらして平均が意味を持つように） ---
  const members = [{name:'田中', key:'A', base:8},{name:'佐藤', key:'B', base:6},{name:'鈴木', key:'C', base:10}];
  const files = [];
  for(const m of members){
    const p = await b.newPage();
    await p.goto(SEL); await p.fill('#staffName', m.name); await p.fill('#targetMonth','2026年7月');
    await p.setInputFiles('#fileMaster', MASTER); await p.waitForTimeout(800);
    const codes = await p.evaluate(()=>ENTRIES.map(e=>e.code));
    const blocks = codes.map((c,i)=>{
      const v = Math.max(0, Math.min(10, m.base + (i%5) - 2));
      return `===SCORE===\nEntryCode: ${c}\n観点①: ${v}\n観点②: ${v}\n観点③: ${v}\n観点④: ${v}\n===END===`;
    }).join('\n\n');
    await p.evaluate((t)=>{ applyCopilot(t); saveState(); render(); }, blocks);
    const out = path.resolve(__dirname, `member_${m.key}.xlsx`);
    const [dl] = await Promise.all([ p.waitForEvent('download'), p.click('#btnXLS') ]);
    await dl.saveAs(out); files.push(out);
    await p.close();
  }

  // --- 集計ツールで3本読み込み ---
  const p = await b.newPage();
  const errors = [];
  p.on('pageerror', e=>errors.push('pageerror: '+e.message));
  p.on('console', m=>{ if(m.type()==='error') errors.push('console.error: '+m.text()); });
  await p.goto(AGG);
  await p.setInputFiles('#fileIn', files); await p.waitForTimeout(1000);

  ok((await p.textContent('#hFiles')).includes('3'), '採点メンバー3名が読み込まれる');
  ok((await p.textContent('#hWin')).replace(/\s/g,'').startsWith('6/6'), '受賞6件が選出される');
  ok((await p.textContent('#hNom')).replace(/\s/g,'').startsWith('10/10'), 'ノミネート10件が選出される');
  ok((await p.locator('tbody tr').count()) === 15, '全15作品が表示される');

  // 平均 = 各人の最終スコアの単純平均（採点した人だけ）
  const top = await p.evaluate(()=>{
    const agg = aggregate();
    const t = agg.filter(a=>a.avg!=null).sort((a,b)=>b.avg-a.avg)[0];
    return {avg:t.avg, scores:t.memberScores.map(x=>x.score), cnt:t.scoredCount};
  });
  const expAvg = Math.round(top.scores.reduce((s,v)=>s+v,0)/top.scores.length*10)/10;
  ok(top.avg === expAvg, `最上位の平均が各人スコアの平均に一致（${top.scores} → ${top.avg}）`);
  ok(top.cnt === 3, '3人とも採点した作品は採点人数3');

  // 手動順位固定：最下位の作品を1位に固定 → 総合1位になる
  const lastCode = await p.evaluate(()=>{ const s=aggregate().filter(a=>a.avg!=null).sort((a,b)=>b.avg-a.avg); return s[s.length-1].code; });
  await p.fill(`.pin[data-code="${lastCode}"]`, '1');
  await p.locator(`.pin[data-code="${lastCode}"]`).dispatchEvent('change');
  await p.waitForTimeout(300);
  const pinnedRank = await p.evaluate((c)=>{ const {ranks}=computeRanks(aggregate()); return ranks[c]; }, lastCode);
  ok(pinnedRank === 1, '手動で1位に固定した作品が総合1位になる');

  // 書き出し
  const [dl] = await Promise.all([ p.waitForEvent('download'), p.click('#btnXLS') ]);
  const outXlsx = path.resolve(__dirname, 'test_agg_out.xlsx');
  await dl.saveAs(outXlsx);
  ok(fs.existsSync(outXlsx), '集計結果Excelが書き出せる');
  fs.unlinkSync(outXlsx);

  ok(errors.length === 0, `JSエラーなし（実際: ${errors.length}件 ${errors.join(' / ')}）`);
  await b.close();
  files.forEach(f=>{ try{ fs.unlinkSync(f); }catch(_){} });
  console.log('\nALL TESTS PASSED');
})().catch(e=>{ console.error(e); process.exit(1); });
