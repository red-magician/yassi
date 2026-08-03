// worker.js — runs the (CPU-heavy) image pipeline off the main thread.
import { extractFeatures } from './features.js';
import { predict } from './model.js';

self.onmessage = (e) => {
  const { imageData, requestId } = e.data;
  try {
    const features = extractFeatures(imageData);
    const result = predict(features);
    self.postMessage({ requestId, ok: true, result });
  } catch (err) {
    self.postMessage({ requestId, ok: false, error: String(err && err.message ? err.message : err) });
  }
};
