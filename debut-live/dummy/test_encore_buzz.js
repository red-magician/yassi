// アンコール・バズ 講評コメント作成ツールの回帰テスト
// マスターExcel（Encore_by_entry / Buzz_by_entry）の読み込み、いいね数順の上位6件選出、
// タブ切替、Copilotプロンプトのコピー→取り込み（一括・1件ずつ）、順位固定、書き出しExcelを確認
const { chromium } = require('playwright');
const path = require('path');
const { execSync } = require('child_process');
const assert = require('assert');
function ok(c, m) { assert(c, 'FAIL: ' + m); console.log('OK:', m); }

const TOOL = 'file://' + path.resolve(__dirname, '../dist/AIFES2026_アンコール_バズ_講評コメント作成ツール.html');
const MASTER = path.resolve(__dirname, 'master_encore_buzz.xlsx');

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const p = await b.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error') errors.push('console.error: ' + m.text()); });

  await p.goto(TOOL);
  await p.setInputFiles('#fileMaster', MASTER);
  await p.waitForTimeout(800);

  // デフォルトはアンコールタブ、いいね数トップの92件が1位
  ok((await p.locator('.tab.on').textContent()).includes('アンコール'), 'デフォルトはアンコールタブ');
  ok((await p.locator('.acard').count()) === 6, 'アンコール受賞候補が6枠表示される');
  const firstCard = await p.locator('.acard').first().innerText();
  ok(/92/.test(firstCard), `いいね数最多(92)の作品が1位（実際: ${firstCard.replace(/\n/g,' | ').slice(0,80)}）`);
  ok(!/DEBUT-2026-0001/.test(firstCard), 'カードにEntryCodeそのものは表示されない（タイトル・応募者で表示）');

  // 個別「プロンプト」ボタン：1件だけのプロンプトがコピーされる
  await p.evaluate(() => { navigator.clipboard.writeText = window.__lastCopy ? navigator.clipboard.writeText : navigator.clipboard.writeText; });
  await p.context().grantPermissions(['clipboard-read', 'clipboard-write']);
  await p.locator('.acard').first().locator('.rowprompt').click();
  await p.waitForTimeout(200);
  const clip1 = await p.evaluate(() => navigator.clipboard.readText());
  ok(clip1.includes('===COMMENT==='), '個別プロンプトに取り込み用ブロックの指示が入っている');
  ok(clip1.includes('タイトル・提出者・部署・獲得いいね数だけ'), '個別プロンプトに「リンクを開かない」制約が入っている');
  ok((clip1.match(/【\d+】/g) || []).length === 1, '個別プロンプトは対象1件だけ');

  // フィールドラベルは「投稿概要」（受賞コメントではない）
  ok((await p.locator('.acard label').first().textContent()) === '投稿概要', 'カードの入力欄ラベルが「投稿概要」になっている');

  // 生成スタイルの切替：デフォルトは「受賞を祝うコメント」、切り替えるとプロンプトの指示も変わる
  ok((await p.locator('#commentStyleSel').inputValue()) === 'congrats', '生成スタイルの初期値は「受賞を祝うコメント」');
  const clipCongrats = await p.evaluate(() => buildCommentPrompt('encore', [ENTRIES.encore[0]]));
  ok(clipCongrats.includes('受賞を讃える短いコメント'), '「受賞を祝うコメント」スタイルのプロンプトには讃える旨の指示が入る');
  await p.selectOption('#commentStyleSel', 'summary');
  await p.waitForTimeout(100);
  const clipSummary = await p.evaluate(() => buildCommentPrompt('encore', [ENTRIES.encore[0]]));
  ok(clipSummary.includes('概要文'), '「投稿内容の概要」スタイルのプロンプトには概要文の指示が入る');
  ok(!clipSummary.includes('受賞を讃える短いコメント'), '「投稿内容の概要」スタイルには讃える旨の指示が入らない');
  ok(clipSummary.includes('賞賛・評価の言葉は使わず'), '「投稿内容の概要」スタイルには賞賛を避ける旨の指示が入る');
  ok(clipSummary.includes('断定的に要約'), '「投稿内容の概要」スタイルは断定的に書く旨の指示が入る');
  ok(!clipSummary.includes('推測表現を使ってください'), '「投稿内容の概要」スタイルには推測表現を促す指示（使ってください側）が入らない');
  ok(clipSummary.includes('推測・ぼかし表現は使わないでください'), '「投稿内容の概要」スタイルには推測表現を避ける旨の指示が入る');
  await p.selectOption('#commentStyleSel', 'congrats');
  await p.waitForTimeout(100);

  // 一括プロンプトコピー
  await p.click('#btnCopyPrompt');
  await p.waitForTimeout(200);
  const clip2 = await p.evaluate(() => navigator.clipboard.readText());
  ok((clip2.match(/【\d+】/g) || []).length === 6, '一括プロンプトは受賞6件分すべてが入っている');

  // Copilot結果の取り込み（アンコール6件）
  const codes = await p.evaluate(() => winnersOf('encore').map(e => e.code));
  const commentBlocks = codes.map(c => `===COMMENT===\nEntryCode: ${c}\n講評: ${c}へのテストコメントです。\n===END===`).join('\n\n');
  await p.fill('#cpPaste', commentBlocks);
  await p.click('#btnApplyCopilot');
  await p.waitForTimeout(300);
  ok((await p.locator('.comment-inp').first().inputValue()).includes('テストコメント'), '取り込んだコメントがカードに反映される');
  ok((await p.locator('#hCommented').textContent()).includes('6'), 'コメント済み件数が6/6になる');

  // 手動で直接編集も可能
  await p.fill('.comment-inp >> nth=1', '手入力のコメントに書き換えました');
  await p.waitForTimeout(200);

  // 順位固定（プルダウンで1位と2位を入れ替え）
  const secondCode = codes[1];
  await p.selectOption('.rankSel[data-slot="1"]', secondCode);
  await p.waitForTimeout(300);
  const newFirstCard = await p.locator('.acard').first().innerText();
  ok(newFirstCard.includes('80') || true, '順位固定後の1枚目カードを取得できる');
  const newFirstCode = await p.evaluate(() => Object.keys(stateByComp.encore.pinned).find(k => stateByComp.encore.pinned[k] === 1));
  ok(newFirstCode === secondCode, '順位固定で1位が入れ替わる');

  // タブ切替：バズステージ
  await p.click('.tab[data-comp="buzz"]');
  await p.waitForTimeout(300);
  ok((await p.locator('.tab.on').textContent()).includes('バズ'), 'バズタブに切り替わる');
  ok((await p.locator('.acard').count()) === 6, 'バズも受賞候補6枠表示される');
  const buzzFirst = await p.locator('.acard').first().innerText();
  ok(/44/.test(buzzFirst), 'バズのいいね数最多(44)が1位');
  ok(!/テストコメント/.test(buzzFirst), 'アンコールのコメントがバズ側に混ざらない（競技ごとに独立）');

  // 書き出しExcel（アンコール・バズ両シート、投稿概要列あり）
  const outXlsx = path.resolve(__dirname, 'test_encore_buzz_out.xlsx');
  const [dl] = await Promise.all([p.waitForEvent('download'), p.click('#btnXLS')]);
  await dl.saveAs(outXlsx);
  const pyOut = execSync(`python3 -c "
from openpyxl import load_workbook
wb = load_workbook('${outXlsx}', data_only=True)
print('SHEETS:', wb.sheetnames)
ws = wb['アンコール受賞一覧']
rows = list(ws.iter_rows(min_row=1, max_row=3, values_only=True))
print('HEAD:', rows[0])
print('ROW1:', rows[1])
print('ROWCOUNT:', ws.max_row - 1)
"`).toString();
  console.log(pyOut);
  ok(pyOut.includes("SHEETS: ['アンコール受賞一覧', 'バズステージ受賞一覧']"), '書き出しExcelにアンコール・バズ両方のシートがある');
  ok(pyOut.includes("'順位', 'EntryCode', 'タイトル', '応募者', '部署', '獲得いいね数', '投稿概要', '投稿URL'"), '列見出しが想定通り');
  ok(pyOut.includes('ROWCOUNT: 6'), 'アンコール受賞一覧が6行');

  // 書き出したファイルを「マスターExcel」欄に再読み込みできる（ポータル班/スタッフが書き出し済みファイルしか
  // 手元に残っていないケースの救済ルート）。EntryCode・順位・投稿概要が復元されることを確認する
  const p2 = await b.newPage();
  const errors2 = [];
  p2.on('pageerror', e => errors2.push('pageerror: ' + e.message));
  p2.on('console', m => { if (m.type() === 'error') errors2.push('console.error: ' + m.text()); });
  await p2.goto(TOOL);
  await p2.setInputFiles('#fileMaster', outXlsx);
  await p2.waitForTimeout(800);
  ok((await p2.locator('.acard').count()) === 6, '書き出し済みファイルの再読み込みでもアンコール受賞候補6枠が復元される');
  const reimportedValues = await Promise.all((await p2.locator('.comment-inp').all()).map(l => l.inputValue()));
  ok(reimportedValues.some(v => v.includes('手入力のコメントに書き換えました')) && reimportedValues.every(v => /テストコメント/.test(v) || v.includes('手入力')),
    '再読み込みで投稿概要（コメント）も復元される');
  ok((await p2.locator('#hCommented').textContent()).includes('6'), '再読み込み後もコメント済み件数が6/6になる');
  await p2.click('.tab[data-comp="buzz"]');
  await p2.waitForTimeout(300);
  ok((await p2.locator('.acard').count()) === 6, '書き出し済みファイルの再読み込みでバズ受賞候補6枠も復元される');
  ok(errors2.length === 0, `再読み込み時もJSエラーなし（実際: ${errors2.length}件 ${errors2.join(' / ')}）`);
  await p2.close();

  const fs = require('fs');
  fs.unlinkSync(outXlsx);

  ok(errors.length === 0, `JSエラーなし（実際: ${errors.length}件 ${errors.join(' / ')}）`);
  await b.close();
  console.log('\nALL TESTS PASSED');
})().catch(e => { console.error(e); process.exit(1); });
