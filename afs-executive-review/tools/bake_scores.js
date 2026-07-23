// 役員審査ツール（build/配下のテンプレート）に、審査員がエクスポートした採点Excel（10_役員向け審査シート）を
// あらかじめ取り込んだ状態で焼き込み、dist/配下に「開くだけでAI事前採点が表示される」HTMLを生成する。
//
// 使い方:
//   NODE_PATH=/opt/node22/lib/node_modules node tools/bake_scores.js <元テンプレート.html> <採点済みExcel.xlsx> <出力先.html>
//
// 実体は、ヘッドレスブラウザでテンプレートを開き、既存の「読み込む（Excel）」機能（#fileIn）を
// そのまま使って取り込ませ、結果の aiData/opsData を HTML に直接埋め込み直しているだけ。
// 取り込みロジック自体（importAI関数）はテンプレート側にあるので、ここでは重複実装しない。
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const [, , templatePath, xlsxPath, outPath] = process.argv;
if (!templatePath || !xlsxPath || !outPath) {
  console.error('使い方: node bake_scores.js <テンプレート.html> <採点済みExcel.xlsx> <出力先.html>');
  process.exit(1);
}

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const p = await b.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  p.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });

  await p.goto('file://' + path.resolve(templatePath));
  await p.setInputFiles('#fileIn', path.resolve(xlsxPath));
  await p.waitForTimeout(800);

  const toastText = await p.textContent('#toast').catch(() => '');
  const info = await p.evaluate(() => ({
    aiData, opsData,
    n: Object.keys(aiData).length,
    entries: ENTRIES.length,
  }));
  console.log(path.basename(templatePath), '| 取込:', toastText, '| aiData:', info.n, '/ ENTRIES:', info.entries, '| JSエラー:', errors.length);
  if (errors.length) console.log('  ', errors.slice(0, 5));

  const html = fs.readFileSync(templatePath, 'utf-8');
  let result = html.replace('let aiData = {};', 'let aiData = ' + JSON.stringify(info.aiData) + ';');
  result = result.replace('let opsData = {};', 'let opsData = ' + JSON.stringify(info.opsData) + ';');
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, result, 'utf-8');
  console.log('  -> 生成:', outPath);

  await p.close();
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
