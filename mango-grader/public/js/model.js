// model.js — mango_grader_model.joblib, ported to JS.
//
// Pipeline is SimpleImputer(mean) -> StandardScaler -> LogisticRegression
// (multinomial/softmax, 3 classes). Coefficients extracted verbatim from
// the joblib bundle (see mango-grader/MODEL_NOTES.md for how). Predicting
// is just linear algebra, so no ML runtime is needed in the browser.

export const FEATURE_NAMES = ['vr_whole', 'blob_largest_frac', 'blob_n'];
export const CLASSES = ['A', 'B', 'C'];

export const IMPUTER_STATISTICS = [83.46676371937748, 98.90746103774146, 1.0350877192982457];
export const SCALER_MEAN = [83.46676371937748, 98.90746103774146, 1.0350877192982457];
export const SCALER_SCALE = [17.311854472259782, 3.396594530211091, 0.18400155231055287];

// coef[classIndex][featureIndex], row order matches CLASSES
export const COEF = [
  [2.89543482688818, 0.13819916663077242, 0.3533092635406199],
  [0.2785271298022595, -0.5785205210531463, 0.22086194802005993],
  [-3.173961956690444, 0.44032135442237225, -0.5741712115606791],
];
export const INTERCEPT = [3.6770860748830883, 1.8687796579299583, -5.5458657328130405];

export const MODEL_META = {
  version: 'v1',
  trained_at: '2026-08-02',
  n_train: 114,
  n_train_by_grade: { A: 100, B: 11, C: 3 },
  cv_macro_f1: 0.701,
  cv_kappa: 0.719,
  cv_accuracy: 0.929,
};

function softmax(scores) {
  const max = Math.max(...scores);
  const exps = scores.map((s) => Math.exp(s - max));
  const sum = exps.reduce((a, b) => a + b, 0);
  return exps.map((e) => e / sum);
}

/**
 * features: {vr_whole, blob_largest_frac, blob_n} as returned by
 * features.js#extractFeatures(), or null if no fruit region was found.
 *
 * Mirrors MangoGrader.predict() in mango_grader.py, including the
 * blob_n===0 rule-based guard (no vivid-red pixels at all -> force C
 * without going through the logistic regression, since the training data
 * never contained a blob_n=0 example and the model extrapolates badly
 * there).
 */
export function predict(features, { confidenceThreshold = 0.55 } = {}) {
  if (features === null) {
    return {
      grade: null,
      proba: null,
      confidence: null,
      needs_review: true,
      features: null,
      // stable code, not user-facing text -- the UI layer (app.js) is
      // responsible for translating this into the active language.
      error: 'no_fruit_detected',
    };
  }

  if (features.blob_n === 0) {
    return {
      grade: 'C',
      proba: { A: 0, B: 0, C: 1 },
      confidence: 1.0,
      needs_review: false,
      features,
      note: 'forced_c_no_vivid_pixels',
    };
  }

  const x = FEATURE_NAMES.map((name, i) => {
    const v = features[name];
    return Number.isFinite(v) ? v : IMPUTER_STATISTICS[i];
  });
  const z = x.map((v, i) => (v - SCALER_MEAN[i]) / SCALER_SCALE[i]);
  const scores = COEF.map((row, c) => row.reduce((acc, w, i) => acc + w * z[i], INTERCEPT[c]));
  const proba = softmax(scores);

  let bestIdx = 0;
  for (let i = 1; i < proba.length; i++) if (proba[i] > proba[bestIdx]) bestIdx = i;
  const confidence = proba[bestIdx];

  const probaDict = {};
  CLASSES.forEach((c, i) => (probaDict[c] = Math.round(proba[i] * 10000) / 10000));

  return {
    grade: CLASSES[bestIdx],
    proba: probaDict,
    confidence,
    needs_review: confidence < confidenceThreshold,
    features,
  };
}
