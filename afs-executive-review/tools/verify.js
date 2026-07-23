// dist/配下のHTMLを実際にヘッドレスブラウザで開き、基本的な健全性を確認する。
// 使い方: NODE_PATH=/opt/node22/lib/node_modules node tools/verify.js dist/*.html
const { chromium } = require('playwright');
const path = require('path');

const files = process.argv.slice(2);
if (!files.length) {
  console.error('使い方: node tools/verify.js <対象HTML...>');
  process.exit(1);
}

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  let allOk = true;
  for (const f of files) {
    const p = await b.newPage();
    const errors = [];
    p.on('pageerror', e => errors.push(e.message));
    p.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    await p.goto('file://' + path.resolve(f));
    await p.waitForTimeout(400);
    const info = await p.evaluate(() => ({
      entries: ENTRIES.length,
      aiN: Object.keys(aiData).length,
      allRanksBlank: Object.values(state).every(s => !s.rank),
      btnCopilotHidden: (() => { const b = document.getElementById('btnCopilot'); return b ? getComputedStyle(b).display === 'none' : null; })(),
      helpAutoShows: document.getElementById('help').classList.contains('on'),
    }));
    const ok = errors.length === 0 && info.allRanksBlank;
    allOk = allOk && ok;
    console.log(`${ok ? 'OK' : 'NG'}  ${path.basename(f)}  ENTRIES=${info.entries} aiData=${info.aiN} ` +
      `順位空欄=${info.allRanksBlank} Copilot取込非表示=${info.btnCopilotHidden} ヘルプ自動表示=${info.helpAutoShows} JSエラー=${errors.length}`);
    if (errors.length) console.log('   ', errors.slice(0, 3));
    await p.close();
  }
  await b.close();
  process.exit(allOk ? 0 : 1);
})().catch(e => { console.error(e); process.exit(1); });
