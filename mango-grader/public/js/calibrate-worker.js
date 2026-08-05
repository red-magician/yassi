// calibrate-worker.js — runs the calibration grid search off the main
// thread and reports incremental progress, since a full grid search over
// many labeled photos is not instant (each photo's fruit-mask extraction
// runs once; the grid search then reuses it for every (a_thr, h_thr)
// candidate, but 340 candidates x many photos' connected-component passes
// still adds up).
import { extractCore } from './features.js';
import { calibrateThresholds, scoreThresholds } from './calibrate.js';

self.onmessage = (e) => {
  const { requestId, items, currentAThr, currentHThr } = e.data;
  try {
    const coreItems = items.map(({ imageData, humanGrade }) => ({
      coreData: extractCore(imageData),
      humanGrade,
    }));
    const noFruitCount = coreItems.filter((it) => it.coreData === null).length;

    const currentScore = scoreThresholds(coreItems, currentAThr, currentHThr);

    const best = calibrateThresholds(coreItems, {
      onProgress: (done, total) => {
        self.postMessage({ requestId, type: 'progress', done, total });
      },
    });

    self.postMessage({
      requestId,
      type: 'done',
      best,
      currentScore,
      noFruitCount,
      nPhotos: items.length,
    });
  } catch (err) {
    self.postMessage({ requestId, type: 'error', error: String(err && err.message ? err.message : err) });
  }
};
