const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const p = await b.newPage();
  const errs=[]; p.on('pageerror',e=>errs.push(e.message)); p.on('console',m=>{if(m.type()==='error')errs.push(m.text());});
  await p.goto('file://'+path.resolve(__dirname,'../dist/AIFES2026_デビューライブ_受賞選定ツール.html'));
  await p.fill('#staffName','検証'); await p.fill('#targetMonth','2026年7月');
  await p.setInputFiles('#fileMaster', path.resolve(__dirname,'master_test.xlsx'));
  await p.waitForTimeout(1000);
  const codes = await p.evaluate(()=>ENTRIES.map(e=>e.code));
  console.log('entries:', codes.length);
  // 疑似Copilot出力（全件・満点10、体裁を少し崩す＋存在しないコード1件）
  const blocks = codes.map(c=>`===SCORE===\nEntryCode: ${c}\n観点①（ハードル・25%）: 10 / 10\n観点②: 10\n観点③: 10\n観点④: 10\n講評: テスト講評\n===END===`).join('\n\n')
    + '\n===SCORE===\nEntryCode: DEBUT-9999-XXXX\n観点①: 5\n===END===';
  // モーダルを開いて貼り付け→取り込む
  await p.click('#btnCopilot'); await p.waitForTimeout(150);
  await p.fill('#cpPaste', blocks); await p.click('#cpImport'); await p.waitForTimeout(300);
  const res = await p.textContent('#cpResult');
  // 検証: 満点入力→ルーブリック100、最終=100+likeBonus+htmlBonus
  const s0 = await p.evaluate(()=>{ const e=ENTRIES[0]; return {code:e.code, scores:scores[e.code], rubric:e.rubricTotal, final:e.finalScore, like:e.likeBonus, html:e.htmlBonus}; });
  const scoredN = await p.evaluate(()=>ENTRIES.filter(e=>e.hasScore).length);
  // 永続化：リロードして残るか
  await p.waitForTimeout(50);
  console.log('取り込み結果:', JSON.stringify(res));
  console.log('先頭:', JSON.stringify(s0), '/ 採点済み', scoredN, '/', codes.length);
  console.log('JSエラー:', errs.length, errs.slice(0,2).join(' | '));
  const pass = /取り込み \d+ 件/.test(res) && /未一致 1/.test(res)
    && JSON.stringify(s0.scores)===JSON.stringify(['10','10','10','10'])
    && s0.rubric===100 && s0.final===100+s0.like+s0.html && scoredN===codes.length && errs.length===0;
  console.log(pass?'\n✅ デビュー Copilot取り込み OK':'\n❌ 要確認');
  await b.close(); process.exit(pass?0:1);
})().catch(e=>{console.error(e);process.exit(1);});
