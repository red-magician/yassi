// ja.js — source-of-truth Japanese strings. Every other language file must
// have exactly the same set of keys (see i18n.js's dev-time key check).
export default {
  'meta.title': 'マンゴー等級判定（試作）',

  'header.title': '🥭 マンゴー等級判定',
  'header.badge': '試作 v1',

  'home.caveat.summary': '⚠ 判定精度についての注意（必読）',
  'home.caveat.item1':
    'このモデルは<strong>2019年撮影の写真</strong>で較正されています。撮影環境（カメラ・照明・背景）が変わると精度が落ちる場合があります。',
  'home.caveat.item2':
    '<strong>表面の着色だけ</strong>を見ています。傷・ヤニによる格下げは判定できません。最終確認は人が行ってください。',
  'home.caveat.item3': '学習データはA級中心（A100/B11/C3）で、<strong>特にC級の判定精度は未知数</strong>です。',
  'home.caveat.item4': '「確信度」が低い判定は自動的に「要確認」と表示されます。',
  'home.caveat.item5':
    '<strong>実写真での検証で、A判定が出にくい傾向を確認済みです。</strong>本番利用の前に撮影環境向けの再較正を強く推奨します（詳細は開発者向け<code>VALIDATION.md</code>）。',

  'home.lead': '無彩色の背景の上に果実を1個だけ置いて撮影してください。',
  'home.captureCamera': '📷 写真を撮る',
  'home.captureGallery': '🖼 アルバムから選ぶ',
  'home.sendLogsLabel': '判定結果をモデル改善のために送信する（画像は送信されません。数値と等級のみ）',
  'home.thresholdStatusPrefix': '現在の判定基準: ',
  'home.openCalibrate': '⚙ 較正モード（スタッフ向け）',
  'home.langLabel': '言語',

  'calibrate.title': '撮影環境向けの較正',
  'calibrate.lead':
    'このモデルは撮影環境（カメラ・照明・背景）が変わると精度が落ちます。実際の撮影環境で正解の等級が分かっているサンプル写真を集めると、その環境向けに判定の色しきい値を選び直せます（各等級20枚程度が目安）。',
  'calibrate.addPhotos': '＋ サンプル写真を追加',
  'calibrate.progressDefault': '計算中…',
  'calibrate.back': '戻る',
  'calibrate.run': '較正を実行',
  'calibrate.reset': '既定の設定に戻す',
  'calibrate.empty': 'まだサンプル写真がありません',
  'calibrate.gradeSelectPlaceholder': '等級を選択',
  'calibrate.progressWithCount': '計算中… ({{done}}/{{total}})',
  'calibrate.resultSummary': '{{n}}枚のサンプル（うち果実未検出 {{noFruit}}枚）で較正しました。',
  'calibrate.resultCurrentScore': '現在の設定 (a={{a}}, h={{h}}) のスコア: {{score}}',
  'calibrate.resultBestScore': '見つかった最良の設定: <strong>a={{a}}, h={{h}}</strong>（スコア {{score}}）',
  'calibrate.resultImproved': '✓ 現在の設定より改善しています。',
  'calibrate.resultNotImproved': '△ 現在の設定と同等かそれ以下でした。サンプルを増やすと変わる可能性があります。',
  'calibrate.apply': 'この設定を適用する',
  'calibrate.applyAlert': '設定を適用しました（a={{a}}, h={{h}}）。',
  'calibrate.failedAlert': '較正に失敗しました: {{error}}',
  'calibrate.resetAlert': '既定の判定基準に戻しました。',
  'calibrate.thresholdDefault': '既定 (a={{a}}, h={{h}})',
  'calibrate.thresholdCustom': 'カスタム (a={{a}}, h={{h}})',

  'loading.text': '判定中…',

  'result.previewAlt': '撮影した写真',
  'result.confidencePrefix': '確信度: ',
  'result.needsReview': '⚠ 確信度が低い判定です。人の目で確認してください。',
  'result.errorHint': '（背景や写り方を変えて再撮影してください）',
  'result.detailsSummary': '詳細を見る',
  'result.wrong': 'この判定は違う',
  'result.retake': 'もう一度撮る',
  'result.gradeUnknown': '？',
  'result.probaLabel': '確率内訳',
  'result.vrWholeLabel': '鮮紅色の面積割合 (vr_whole)',
  'result.blobFracLabel': '最大連結成分の割合 (blob_largest_frac)',
  'result.blobNLabel': '連結成分の数 (blob_n)',
  'result.gradeLabel.A': '赤秀 A',
  'result.gradeLabel.B': '黒秀 B',
  'result.gradeLabel.C': '白箱 C',
  'result.processFailedAlert': '画像の処理に失敗しました: {{error}}',
  'result.correctionSentAlert': '訂正を送信しました。ありがとうございます。',
  'result.correctionFailedAlert': '送信に失敗しました（オフラインの可能性があります）。',
  'result.error.no_fruit_detected': '果実領域を検出できませんでした',
  'result.note.forced_c_no_vivid_pixels': '鮮紅色画素が検出されなかったため、判定モデルを介さずCとしました',

  'correct.title': '正しい等級を選んでください',
  'correct.hasDefect': '傷・ヤニなど色以外の理由で等級が下がっている',
  'correct.cancel': 'キャンセル',
  'correct.submit': '送信',

  'footer.text': '色（表面等級）のみの試作判定です。最終等級は人の目で確認してください。',

  'grade.A': 'A（赤秀）',
  'grade.B': 'B（黒秀）',
  'grade.C': 'C（白箱）',
};
