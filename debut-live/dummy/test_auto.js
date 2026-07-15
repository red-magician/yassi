// 自動集計競技ツール（Buzz/シーンメーカー/クルーアワード）の回帰テスト
// 事前に make_dummy_auto.py を実行して master_auto.xlsx を用意しておくこと
// 実行: NODE_PATH=/opt/node22/lib/node_modules node test_auto.js
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const assert = require('assert');
function ok(c,m){ assert(c,'FAIL: '+m); console.log('OK:', m); }

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage();
  const errors=[];
  page.on('pageerror', e=>errors.push('pageerror: '+e.message));
  page.on('console', m=>{ if(m.type()==='error') errors.push('console.error: '+m.text()); });

  const file = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_自動集計競技_受賞選定ツール.html');
  await page.goto(file);
  await page.fill('#staffName','城間');
  await page.fill('#period','最終');
  await page.setInputFiles('#fileMaster', path.resolve(__dirname, 'master_auto.xlsx'));
  await page.waitForTimeout(900);

  // === Buzz ===
  ok((await page.textContent('#hPeople')).includes('8'), 'Buzz: 対象8名が集計される');
  // 04_受賞者マスタで Endo が buzz 受賞済み → 除外される
  ok((await page.textContent('#hExcl')).trim().startsWith('1'), 'Buzz: 04_受賞者マスタのEndoが同競技受賞済みで除外される');
  const endoRow = await page.locator('tbody tr', { hasText: 'Endo' }).first().innerText();
  ok(endoRow.includes('受賞済み'), 'Buzz: Endoの行に受賞済みバッジ');
  // 1位はBaba(55/平均55)？ 平均タイブレークの確認：Aoki合計60・平均20、Baba合計55・平均55 → 合計順ではAoki1位
  const top1 = await page.locator('.acard[data-key] .ainfo b').first().innerText();
  ok(top1==='Aoki, Taro', `Buzz: 合計いいね最上位はAoki（実際: ${top1}）`);
  // Chiba は合計50だが平均5 → 上位内。平均タイブレークは同点時のみなので合計順で確認だけ
  const buzzExport = await downloadXLSX(page);
  ok(buzzExport, 'Buzz: Excel書き出しできる');

  // === シーンメーカー ===
  await page.click('.tab[data-comp="scene"]');
  await page.waitForTimeout(400);
  ok((await page.textContent('#hPeople')).includes('6'), 'Scene: 対象6名（IsSceneEligible）');
  // 通期累計いいね：Ito48が最上位（solo投稿のlikes48。scene投稿自体は0）
  const sTop = await page.locator('.acard[data-key] .ainfo b').first().innerText();
  ok(sTop==='Ito, Aoi', `Scene: 通期累計いいね最上位はIto（実際: ${sTop}）`);
  // scene投稿のlikesは0だが、全競技横断で集計されている（scene投稿のみなら0のはず）
  const itoCard = await page.locator('.acard[data-key]').first().innerText();
  const m = itoCard.match(/通期累計いいね\s*(\d+)/);
  ok(m && Number(m[1]) >= 40, `Scene: 全競技横断の累計いいねが反映されている（scene投稿のみでない・実際: ${m&&m[1]}）`);

  // === クルーアワード ===
  await page.click('.tab[data-comp="crew"]');
  await page.waitForTimeout(400);
  ok(await page.locator('#mergePanel').count()===1, 'Crew: 名寄せパネルが表示される');
  // 名寄せ前：「城間 康」「城間さん」が別カウント
  const beforeShiroma = await crewCount(page, '城間 康');
  const beforeShiromaSan = await crewCount(page, '城間さん');
  ok(beforeShiroma!==null && beforeShiromaSan!==null, 'Crew: 生の名前が一覧に出る');
  // 「城間さん」の統合先に「城間 康」を入力してマージ
  const canonInput = page.locator('.canon-in[data-raw="城間さん"]');
  await canonInput.fill('城間 康');
  await canonInput.dispatchEvent('change');
  await page.waitForTimeout(300);
  // ゴミ「くぁwせdrftgy」を無効化
  const invCb = page.locator('.invalid-in[data-raw="くぁwせdrftgy"]');
  await invCb.check();
  await invCb.dispatchEvent('change');
  await page.waitForTimeout(300);
  // マージ後：城間 康 の記載数が増えているはず（城間さん分が合流）
  const afterShiroma = await page.locator('tbody tr', { hasText: '城間 康' }).first().innerText();
  ok(/城間 康/.test(afterShiroma), 'Crew: マージ後も城間 康が集計に残る');
  const crewExport = await downloadXLSX(page);
  ok(crewExport, 'Crew: Excel書き出しできる');

  ok(errors.length===0, `JSエラーなし（実際: ${errors.length}件 ${errors.join(' / ')}）`);
  await browser.close();
  console.log('\nALL TESTS PASSED');
})().catch(e=>{ console.error(e); process.exit(1); });

async function downloadXLSX(page){
  const [d] = await Promise.all([ page.waitForEvent('download'), page.click('#btnXLS') ]);
  const p = path.resolve(__dirname, 'test_auto_out.xlsx');
  await d.saveAs(p); const ok = fs.existsSync(p); fs.unlinkSync(p); return ok;
}
async function crewCount(page, raw){
  const loc = page.locator(`.merge-tbl tr`, { hasText: raw });
  if(await loc.count()===0) return null;
  return true;
}
