// features.js — direct port of mango_grader.py's _fruit_mask() + extract_features()
import { computeInitialMask, computeLabAB, erode, dilate, connectedComponents } from './imaging.js';

export const MAXPX = 1200;
export const A_THR_DEFAULT = 28;
export const H_THR_DEFAULT = 45;

function sum(arr) {
  let s = 0;
  for (let i = 0; i < arr.length; i++) s += arr[i];
  return s;
}

function fruitMask(imageData, w, h) {
  let m = computeInitialMask(imageData);
  // MORPH_OPEN, kernel ones(5,5), iterations=2
  m = erode(m, w, h, 5, 2);
  m = dilate(m, w, h, 5, 2);
  // MORPH_CLOSE, kernel ones(9,9), iterations=3
  m = dilate(m, w, h, 9, 3);
  m = erode(m, w, h, 9, 3);

  const { labels, areas } = connectedComponents(m, w, h);
  if (areas.length === 0) return null;
  let bestLabel = 1, bestArea = areas[0];
  for (let i = 1; i < areas.length; i++) {
    if (areas[i] > bestArea) { bestArea = areas[i]; bestLabel = i + 1; }
  }
  let mask = new Uint8Array(w * h);
  for (let i = 0; i < mask.length; i++) mask[i] = labels[i] === bestLabel ? 1 : 0;

  // MORPH_CLOSE, kernel ones(15,15), iterations=3
  mask = dilate(mask, w, h, 15, 3);
  mask = erode(mask, w, h, 15, 3);
  return mask;
}

/**
 * imageData: ImageData-like {data:Uint8ClampedArray(RGBA), width, height}
 * already downscaled so max(width,height) <= MAXPX (caller's job, matching
 * the PIL resize the Python version does before extract_features()).
 *
 * Returns {vr_whole, blob_largest_frac, blob_n, n_px} or null if no fruit
 * region could be found (mirrors extract_features() returning None).
 */
export function extractFeatures(imageData, aThr = A_THR_DEFAULT, hThr = H_THR_DEFAULT) {
  const w = imageData.width, h = imageData.height;
  const mask = fruitMask(imageData, w, h);
  if (mask === null) return null;
  const maskSum = sum(mask);
  if (maskSum < 5000) return null;

  const er = erode(mask, w, h, 9, 3);
  const erSum = sum(er);
  const core = erSum > maskSum * 0.3 ? er : mask;
  const nCore = sum(core);

  const { aArr, bArr } = computeLabAB(imageData);
  const vivid = new Uint8Array(w * h);
  let vividCount = 0;
  const RAD2DEG = 180 / Math.PI;
  for (let i = 0; i < core.length; i++) {
    if (!core[i]) continue;
    const a = aArr[i], b = bArr[i];
    const hue = Math.atan2(b, a) * RAD2DEG;
    if (a > aThr && hue < hThr) {
      vivid[i] = 1;
      vividCount++;
    }
  }
  const vrWhole = (vividCount / nCore) * 100;

  const { areas: vareas } = connectedComponents(vivid, w, h);
  let blobLargestFrac = 0, blobN = 0;
  if (vareas.length > 0) {
    let maxArea = 0;
    for (const a of vareas) if (a > maxArea) maxArea = a;
    blobLargestFrac = (maxArea / Math.max(vividCount, 1)) * 100;
    const thresh = nCore * 0.005;
    blobN = vareas.filter((a) => a > thresh).length;
  }

  return { vr_whole: vrWhole, blob_largest_frac: blobLargestFrac, blob_n: blobN, n_px: nCore };
}
