// zh.js — machine-translation-quality Simplified Chinese strings. Swap
// these out with professionally reviewed copy whenever that's available;
// the key set must stay identical to ja.js.
export default {
  'meta.title': '芒果等级判定（试用版）',

  'header.title': '🥭 芒果等级判定',
  'header.badge': '试用版 v1',

  'home.caveat.summary': '⚠ 判定结果的使用方法',
  'home.caveat.item1':
    '该模型只判断<strong>表面颜色</strong>。无法判定因伤痕、树脂痕迹导致的降级，<strong>最终等级请由人工确认。</strong>',
  'home.caveat.item2': '显示为“需要确认”的判定，请务必由人工核实。',
  'home.caveat.item3': '这是<strong>试用版</strong>，判定结果请作为参考使用。',

  'home.lead': '请将单个果实放在无彩色背景上拍摄。',
  'home.captureCamera': '📷 拍照',
  'home.captureGallery': '🖼 从相册选择',
  'home.sendLogsLabel': '发送判定结果以帮助改进模型（不发送照片，仅发送数值和等级）',
  'home.thresholdStatusPrefix': '当前判定基准: ',
  'home.openCalibrate': '⚙ 校准模式（员工专用）',
  'home.langLabel': '语言',

  'calibrate.title': '针对拍摄环境的校准',
  'calibrate.lead':
    '当拍摄环境（相机、光线、背景）发生变化时，该模型的精度会下降。收集在实际拍摄环境中已知正确等级的样本照片后，可以为该环境重新选择判定用的颜色阈值（建议每个等级约20张）。',
  'calibrate.notice.summary': '模型的前提与已知局限（员工专用）',
  'calibrate.notice.item1':
    '该模型是根据<strong>2019年拍摄的照片</strong>校准的。如果拍摄环境（相机、光线、背景）不同，精度可能会下降。',
  'calibrate.notice.item2': '训练数据以A级为主（A100/B11/C3），<strong>尤其是C级的判定精度尚不明确</strong>。',
  'calibrate.notice.item3':
    '<strong>正式使用前，强烈建议针对本拍摄环境重新校准。</strong>请收集已知正确等级的样本照片，并按下方步骤执行校准。',
  'calibrate.notice.item4': '验证的详细内容与数值，请参阅开发者文档<code>VALIDATION.md</code>。',
  'calibrate.addPhotos': '＋ 添加样本照片',
  'calibrate.progressDefault': '计算中…',
  'calibrate.back': '返回',
  'calibrate.run': '执行校准',
  'calibrate.reset': '恢复默认设置',
  'calibrate.empty': '暂无样本照片',
  'calibrate.gradeSelectPlaceholder': '选择等级',
  'calibrate.progressWithCount': '计算中… ({{done}}/{{total}})',
  'calibrate.resultSummary': '已使用{{n}}张样本照片进行校准（其中{{noFruit}}张未检测到果实）。',
  'calibrate.resultCurrentScore': '当前设置 (a={{a}}, h={{h}}) 的得分: {{score}}',
  'calibrate.resultBestScore': '找到的最佳设置: <strong>a={{a}}, h={{h}}</strong>（得分 {{score}}）',
  'calibrate.resultImproved': '✓ 比当前设置有所改善。',
  'calibrate.resultNotImproved': '△ 与当前设置相同或更差。增加样本数量可能会改变结果。',
  'calibrate.apply': '应用此设置',
  'calibrate.applyAlert': '已应用设置（a={{a}}, h={{h}}）。',
  'calibrate.failedAlert': '校准失败: {{error}}',
  'calibrate.resetAlert': '已恢复为默认判定设置。',
  'calibrate.thresholdDefault': '默认 (a={{a}}, h={{h}})',
  'calibrate.thresholdCustom': '自定义 (a={{a}}, h={{h}})',

  'loading.text': '判定中…',

  'result.previewAlt': '拍摄的照片',
  'result.confidencePrefix': '置信度: ',
  'result.needsReview': '⚠ 置信度较低的判定结果，请由人工确认。',
  'result.errorHint': '（请更换背景或拍摄角度后重新拍摄）',
  'result.detailsSummary': '查看详情',
  'result.wrong': '此判定有误',
  'result.retake': '重新拍摄',
  'result.gradeUnknown': '？',
  'result.probaLabel': '概率明细',
  'result.vrWholeLabel': '鲜红色面积占比 (vr_whole)',
  'result.blobFracLabel': '最大连通区域占比 (blob_largest_frac)',
  'result.blobNLabel': '连通区域数量 (blob_n)',
  'result.gradeLabel.A': 'A级',
  'result.gradeLabel.B': 'B级',
  'result.gradeLabel.C': 'C级',
  'result.processFailedAlert': '图像处理失败: {{error}}',
  'result.correctionSentAlert': '订正已提交，谢谢！',
  'result.correctionFailedAlert': '提交失败（可能处于离线状态）。',
  'result.error.no_fruit_detected': '未能检测到果实区域',
  'result.note.forced_c_no_vivid_pixels': '由于未检测到鲜红色像素，未经过判定模型直接判定为C级',

  'correct.title': '请选择正确的等级',
  'correct.hasDefect': '因伤痕、树脂痕迹等非颜色原因导致等级下降',
  'correct.cancel': '取消',
  'correct.submit': '提交',

  'footer.text': '这是仅判定表面颜色（表面等级）的试用版。最终等级请由人工确认。',

  'grade.A': 'A级',
  'grade.B': 'B级',
  'grade.C': 'C级',
};
