// calibrate.js — port of mango_grader.py's calibrate_thresholds().
//
// Grid-searches (a_thr, h_thr) against a set of photos with known human
// grades, scoring each candidate with the same simple JA-rule classifier
// the Python version uses for calibration (NOT the logistic regression —
// calibration only re-picks the vivid-red color thresholds; retraining the
// classifier on the new thresholds is a separate, offline step matching
// the original retrain.py workflow).
import { vividFeaturesFromCore } from './features.js';

// range(12, 45, 2) / range(20, 60, 2) from mango_grader.py, ported literally.
function rangeStep(start, stop, step) {
  const out = [];
  for (let v = start; v < stop; v += step) out.push(v);
  return out;
}
export const A_GRID_DEFAULT = rangeStep(12, 45, 2);
export const H_GRID_DEFAULT = rangeStep(20, 60, 2);

function ruleGrade(vrWhole) {
  if (vrWhole >= 70) return 'A';
  if (vrWhole >= 30) return 'B';
  return 'C';
}

// sklearn f1_score(average='macro', labels=['C','B','A'], zero_division=0)
export function macroF1(yTrue, yPred, labels = ['C', 'B', 'A']) {
  let total = 0;
  for (const label of labels) {
    let tp = 0, fp = 0, fn = 0;
    for (let i = 0; i < yTrue.length; i++) {
      const t = yTrue[i] === label, p = yPred[i] === label;
      if (t && p) tp++;
      else if (!t && p) fp++;
      else if (t && !p) fn++;
    }
    const precision = tp + fp === 0 ? 0 : tp / (tp + fp);
    const recall = tp + fn === 0 ? 0 : tp / (tp + fn);
    const f1 = precision + recall === 0 ? 0 : (2 * precision * recall) / (precision + recall);
    total += f1;
  }
  return total / labels.length;
}

/**
 * items: [{coreData, humanGrade}], coreData from features.js#extractCore()
 * (null means no fruit region was found in that photo — scored as a forced
 * "C" prediction, mirroring calibrate_thresholds()'s `"C" if f is None`).
 */
export function scoreThresholds(items, aThr, hThr) {
  const preds = [], labels = [];
  for (const { coreData, humanGrade } of items) {
    const pred = coreData === null ? 'C' : ruleGrade(vividFeaturesFromCore(coreData, aThr, hThr).vr_whole);
    preds.push(pred);
    labels.push(humanGrade);
  }
  return macroF1(labels, preds);
}

/**
 * onProgress(done, total) is called after each grid point (aGrid.length *
 * hGrid.length calls total) so the UI can show a progress bar — a full
 * grid search over many photos is not instant.
 */
export function calibrateThresholds(items, { aGrid = A_GRID_DEFAULT, hGrid = H_GRID_DEFAULT, onProgress } = {}) {
  let best = { aThr: null, hThr: null, score: -1 };
  const total = aGrid.length * hGrid.length;
  let done = 0;
  for (const aThr of aGrid) {
    for (const hThr of hGrid) {
      const score = scoreThresholds(items, aThr, hThr);
      if (score > best.score) best = { aThr, hThr, score };
      done++;
      if (onProgress) onProgress(done, total);
    }
  }
  return best;
}
