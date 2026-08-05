// imaging.js
//
// OpenCV-faithful reimplementation of the image-processing steps used by
// the Python reference (mango_grader.py / _fruit_mask + extract_features).
// Only the parts actually needed by that pipeline are ported:
//   - HSV S/V (used only for background/foreground thresholding, no hue)
//   - CIE Lab a*/b* (OpenCV's documented sRGB->Lab algorithm, D65)
//   - binary erode/dilate with a flat rectangular (all-ones) structuring
//     element, matching cv2.morphologyEx(..., iterations=n)
//   - 8-connectivity connected component labeling
//
// Erosion/dilation by the same flat k x k SE repeated `iterations` times is
// mathematically identical to a single erosion/dilation by the Minkowski
// sum of those SEs, which for a square of size k is a square of size
// (k-1)*iterations + 1. That lets each erode()/dilate() call below run as
// ONE separable min/max pass instead of looping, while staying exact.

function srgbToLinear(c) {
  c /= 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function fLab(t) {
  return t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116;
}

// S>60 & V>40 foreground mask (OpenCV RGB2HSV, 8-bit scale, S/V only).
export function computeInitialMask(imageData) {
  const { data, width, height } = imageData;
  const n = width * height;
  const mask = new Uint8Array(n);
  for (let i = 0; i < n; i++) {
    const o = i * 4;
    const r = data[o], g = data[o + 1], b = data[o + 2];
    const maxc = Math.max(r, g, b), minc = Math.min(r, g, b);
    const v = maxc;
    const s = maxc === 0 ? 0 : Math.round(((maxc - minc) * 255) / maxc);
    mask[i] = s > 60 && v > 40 ? 1 : 0;
  }
  return mask;
}

// True (unshifted) Lab a*/b*, quantized the same way OpenCV quantizes to
// 8-bit (scale, round, clip to 0-255, then the caller's -128 recovers the
// signed range) so threshold comparisons match the Python model.
export function computeLabAB(imageData) {
  const { data, width, height } = imageData;
  const n = width * height;
  const aArr = new Int16Array(n);
  const bArr = new Int16Array(n);
  const Xn = 0.950456, Yn = 1.0, Zn = 1.088754;
  for (let i = 0; i < n; i++) {
    const o = i * 4;
    const R = srgbToLinear(data[o]), G = srgbToLinear(data[o + 1]), B = srgbToLinear(data[o + 2]);
    const X = 0.412453 * R + 0.35758 * G + 0.180423 * B;
    const Y = 0.212671 * R + 0.71516 * G + 0.072169 * B;
    const Z = 0.019334 * R + 0.119193 * G + 0.950227 * B;
    const fx = fLab(X / Xn), fy = fLab(Y / Yn), fz = fLab(Z / Zn);
    let aVal = 500 * (fx - fy) + 128;
    let bVal = 200 * (fy - fz) + 128;
    aVal = Math.min(255, Math.max(0, Math.round(aVal)));
    bVal = Math.min(255, Math.max(0, Math.round(bVal)));
    aArr[i] = aVal - 128;
    bArr[i] = bVal - 128;
  }
  return { aArr, bArr };
}

// O(n) sliding min/max over a 1D array with a clipped (not padded) window
// of radius r: window at i covers [max(0,i-r), min(n-1,i+r)].
function slidingMinMax(src, n, r, mode) {
  const out = new Uint8Array(n);
  const dq = new Int32Array(n);
  let head = 0, tail = 0, nextPush = 0;
  const better = mode === 'min' ? (x, y) => x <= y : (x, y) => x >= y;
  for (let i = 0; i < n; i++) {
    const hi = Math.min(n - 1, i + r);
    while (nextPush <= hi) {
      while (tail > head && better(src[nextPush], src[dq[tail - 1]])) tail--;
      dq[tail++] = nextPush;
      nextPush++;
    }
    const lo = Math.max(0, i - r);
    while (dq[head] < lo) head++;
    out[i] = src[dq[head]];
  }
  return out;
}

function boxMinMax(mask, w, h, radius, mode) {
  // rows
  let tmp = new Uint8Array(w * h);
  const row = new Uint8Array(w);
  for (let y = 0; y < h; y++) {
    const off = y * w;
    row.set(mask.subarray(off, off + w));
    tmp.set(slidingMinMax(row, w, radius, mode), off);
  }
  // columns
  const out = new Uint8Array(w * h);
  const col = new Uint8Array(h);
  for (let x = 0; x < w; x++) {
    for (let y = 0; y < h; y++) col[y] = tmp[y * w + x];
    const res = slidingMinMax(col, h, radius, mode);
    for (let y = 0; y < h; y++) out[y * w + x] = res[y];
  }
  return out;
}

export function erode(mask, w, h, k, iterations = 1) {
  const eff = (k - 1) * iterations + 1;
  return boxMinMax(mask, w, h, (eff - 1) >> 1, 'min');
}

export function dilate(mask, w, h, k, iterations = 1) {
  const eff = (k - 1) * iterations + 1;
  return boxMinMax(mask, w, h, (eff - 1) >> 1, 'max');
}

// 8-connectivity labeling. label 0 = background. Returns areas[i] = pixel
// count for label i+1 (mirrors cv2.connectedComponentsWithStats semantics
// minus the background row).
export function connectedComponents(mask, w, h) {
  const n = w * h;
  const labels = new Int32Array(n);
  const areas = [];
  const stack = new Int32Array(n);
  let currentLabel = 0;
  for (let start = 0; start < n; start++) {
    if (mask[start] === 0 || labels[start] !== 0) continue;
    currentLabel++;
    let sp = 0;
    stack[sp++] = start;
    labels[start] = currentLabel;
    let area = 0;
    while (sp > 0) {
      const idx = stack[--sp];
      area++;
      const x = idx % w, y = (idx / w) | 0;
      for (let dy = -1; dy <= 1; dy++) {
        const ny = y + dy;
        if (ny < 0 || ny >= h) continue;
        for (let dx = -1; dx <= 1; dx++) {
          if (dx === 0 && dy === 0) continue;
          const nx = x + dx;
          if (nx < 0 || nx >= w) continue;
          const nidx = ny * w + nx;
          if (mask[nidx] !== 0 && labels[nidx] === 0) {
            labels[nidx] = currentLabel;
            stack[sp++] = nidx;
          }
        }
      }
    }
    areas.push(area);
  }
  return { labels, areas };
}
