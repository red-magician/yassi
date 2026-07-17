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
  // 全件に点数+講評、うち2件だけ受賞理由
  const blocks = codes.map((c,idx)=>{
    let blk=`===SCORE===\nEntryCode: ${c}\n観点①: 8\n観点②: 10\n観点③: 6\n観点④: 8\n`;
    if(idx<2) blk+=`受賞理由: ${c}の受賞理由テスト\n`;
    blk+=`講評: ${c}の講評テスト全件\n===END===`;
    return blk;
  }).join('\n\n');
  await p.click('#btnCopilot'); await p.waitForTimeout(120);
  await p.fill('#cpPaste', blocks); await p.click('#cpImport'); await p.waitForTimeout(300);
  const res = await p.textContent('#cpResult');
  const stats = await p.evaluate(()=>({
    scored: ENTRIES.filter(e=>e.hasScore).length,
    withComment: Object.values(notes).filter(n=>n.comment).length,
    withReason: Object.values(notes).filter(n=>n.reason).length,
    total: ENTRIES.length,
  }));
  // 表に講評コメント列(textarea)があるか
  const taCount = await p.locator('.row-comment').count();
  const firstComment = await p.locator('.row-comment').first().inputValue();
  // エクスポートのallRowsに講評コメント列があるか
  const allHead = await p.evaluate(()=>allRows()[0]);
  const hasCol = allHead.includes('講評コメント');
  console.log('取り込み結果:', res);
  console.log('stats:', JSON.stringify(stats), '/ 講評列textarea数:', taCount, '/ 先頭コメント:', JSON.stringify(firstComment.slice(0,20)));
  console.log('allRows に講評コメント列:', hasCol);
  console.log('JSエラー:', errs.length, errs.slice(0,2).join(' | '));
  const pass = /講評 \d+件/.test(res) && stats.scored===stats.total && stats.withComment===stats.total && stats.withReason===2
    && taCount===stats.total && firstComment.includes('講評テスト') && hasCol && errs.length===0;
  console.log(pass?'\n✅ デビュー 講評全件＋受賞理由 取り込み OK':'\n❌ 要確認');
  await b.close(); process.exit(pass?0:1);
})().catch(e=>{console.error(e);process.exit(1);});
