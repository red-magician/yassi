// 2人の作業者が独立して受賞選定ツールを操作した結果を再現し、突合テスト用のExcelを書き出す
const { chromium } = require('playwright');
const path = require('path');

async function runStaff(browser, { staffName, masterFile, overrideSlot1 }) {
  const page = await browser.newPage();
  const filePath = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_デビューライブ_受賞選定ツール.html');
  await page.goto(filePath);
  await page.fill('#staffName', staffName);
  await page.fill('#targetMonth', '2026年7月');
  await page.setInputFiles('#fileMaster', path.resolve(__dirname, masterFile));
  await page.waitForTimeout(800);

  if (overrideSlot1) {
    // 1位を、自動選出とは別のエントリーに手動で入れ替える（不一致を再現）
    const rankSelects = page.locator('.row-rank');
    const n = await rankSelects.count();
    for (let i = 0; i < n; i++) {
      const sel = rankSelects.nth(i);
      if (await sel.isEnabled() && (await sel.inputValue()) === '0') {
        await sel.selectOption('1');
        break;
      }
    }
  }

  // 全スロットの受賞理由・講評コメントを埋める
  const reasonBoxes = page.locator('.note-reason');
  const commentBoxes = page.locator('.note-comment');
  const rc = await reasonBoxes.count();
  for (let i = 0; i < rc; i++) {
    await reasonBoxes.nth(i).fill(`${staffName}の受賞理由${i + 1}`);
    await commentBoxes.nth(i).fill(`${staffName}の講評コメント${i + 1}`);
  }

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.click('#btnXLS'),
  ]);
  // ファイル名は headless Chromium の非ASCII名バグを避けるため常にASCIIにする（中身の作業者名は保持される）
  const asciiName = staffName === '田中' ? 'staffA' : 'staffB';
  const savePath = path.resolve(__dirname, `${asciiName}.xlsx`);
  await download.saveAs(savePath);
  console.log('saved:', savePath);
  await page.close();
}

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  await runStaff(browser, { staffName: '田中', masterFile: 'master_test.xlsx', overrideSlot1: false });
  await runStaff(browser, { staffName: '佐藤', masterFile: 'master_test_staffB.xlsx', overrideSlot1: true });
  await browser.close();
})();
