// en.js — machine-translation-quality English strings. Swap these out with
// professionally reviewed copy whenever that's available; the key set must
// stay identical to ja.js.
export default {
  'meta.title': 'Mango Grade Checker (prototype)',

  'header.title': '🥭 Mango Grade Checker',
  'header.badge': 'Prototype v1',

  'home.caveat.summary': '⚠ About accuracy (please read)',
  'home.caveat.item1':
    'This model was calibrated on photos taken in <strong>2019</strong>. Accuracy may drop if the shooting conditions (camera, lighting, background) are different.',
  'home.caveat.item2':
    'It only looks at <strong>surface color</strong>. It cannot detect downgrades from bruises or sap stains — please have a person do the final check.',
  'home.caveat.item3':
    'The training data was mostly Grade A (A100/B11/C3), so <strong>Grade C accuracy in particular is largely unverified</strong>.',
  'home.caveat.item4': 'Low-confidence predictions are automatically flagged as "needs review".',
  'home.caveat.item5':
    '<strong>Testing on real photos found that Grade A rarely comes out.</strong> We strongly recommend recalibrating for your shooting environment before real-world use (see <code>VALIDATION.md</code> for developers).',

  'home.lead': 'Place a single fruit on a neutral-colored background and take a photo.',
  'home.captureCamera': '📷 Take a photo',
  'home.captureGallery': '🖼 Choose from album',
  'home.sendLogsLabel': 'Send results to help improve the model (no photo is sent — only numbers and grade)',
  'home.thresholdStatusPrefix': 'Current grading settings: ',
  'home.openCalibrate': '⚙ Calibration mode (for staff)',
  'home.langLabel': 'Language',

  'calibrate.title': 'Calibrate for your shooting environment',
  'calibrate.lead':
    'This model loses accuracy when the shooting conditions (camera, lighting, background) change. Collecting sample photos with known correct grades from your actual shooting environment lets you re-select the color thresholds for that environment (about 20 photos per grade is a good target).',
  'calibrate.addPhotos': '＋ Add sample photos',
  'calibrate.progressDefault': 'Calculating…',
  'calibrate.back': 'Back',
  'calibrate.run': 'Run calibration',
  'calibrate.reset': 'Reset to default settings',
  'calibrate.empty': 'No sample photos yet',
  'calibrate.gradeSelectPlaceholder': 'Select grade',
  'calibrate.progressWithCount': 'Calculating… ({{done}}/{{total}})',
  'calibrate.resultSummary': 'Calibrated using {{n}} sample photo(s) ({{noFruit}} with no fruit detected).',
  'calibrate.resultCurrentScore': 'Score for current settings (a={{a}}, h={{h}}): {{score}}',
  'calibrate.resultBestScore': 'Best settings found: <strong>a={{a}}, h={{h}}</strong> (score {{score}})',
  'calibrate.resultImproved': '✓ This is an improvement over the current settings.',
  'calibrate.resultNotImproved':
    '△ This is about the same or worse than the current settings. Adding more samples may change the result.',
  'calibrate.apply': 'Use these settings',
  'calibrate.applyAlert': 'Settings applied (a={{a}}, h={{h}}).',
  'calibrate.failedAlert': 'Calibration failed: {{error}}',
  'calibrate.resetAlert': 'Reset to the default grading settings.',
  'calibrate.thresholdDefault': 'Default (a={{a}}, h={{h}})',
  'calibrate.thresholdCustom': 'Custom (a={{a}}, h={{h}})',

  'loading.text': 'Grading…',

  'result.previewAlt': 'Photo taken',
  'result.confidencePrefix': 'Confidence: ',
  'result.needsReview': '⚠ Low-confidence result. Please double-check by eye.',
  'result.errorHint': '(try retaking the photo with a different background or angle)',
  'result.detailsSummary': 'Show details',
  'result.wrong': 'This grade is wrong',
  'result.retake': 'Take another photo',
  'result.gradeUnknown': '?',
  'result.probaLabel': 'Probability breakdown',
  'result.vrWholeLabel': 'Vivid-red area ratio (vr_whole)',
  'result.blobFracLabel': 'Largest connected-region ratio (blob_largest_frac)',
  'result.blobNLabel': 'Number of connected regions (blob_n)',
  'result.gradeLabel.A': 'Grade A',
  'result.gradeLabel.B': 'Grade B',
  'result.gradeLabel.C': 'Grade C',
  'result.processFailedAlert': 'Failed to process the image: {{error}}',
  'result.correctionSentAlert': 'Correction submitted. Thank you!',
  'result.correctionFailedAlert': 'Failed to submit (you may be offline).',
  'result.error.no_fruit_detected': 'Could not detect a fruit region',
  'result.note.forced_c_no_vivid_pixels':
    'No vivid-red pixels were detected, so this was graded C directly without going through the model',

  'correct.title': 'Select the correct grade',
  'correct.hasDefect': 'Downgraded for a non-color reason (bruise, sap stain, etc.)',
  'correct.cancel': 'Cancel',
  'correct.submit': 'Submit',

  'footer.text': 'This is a prototype that only grades surface color. Please have a person confirm the final grade.',

  'grade.A': 'A',
  'grade.B': 'B',
  'grade.C': 'C',
};
