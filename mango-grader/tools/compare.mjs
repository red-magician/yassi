// tools/compare.mjs — validation helper (not part of the deployed app).
//
// Feeds the .ppm dumps produced by dump_ground_truth.py through the JS
// port and diffs the result against the Python ground truth.
//
// Usage:
//   python tools/dump_ground_truth.py <photos_dir> <out_dir>
//   node tools/compare.mjs <out_dir>
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { extractFeatures } from '../public/js/features.js';
import { predict } from '../public/js/model.js';

const outDir = process.argv[2];
if (!outDir) {
  console.error('usage: node compare.mjs <out_dir produced by dump_ground_truth.py>');
  process.exit(1);
}

function readPPM(file) {
  const buf = fs.readFileSync(file);
  let offset = 0;
  function readLine() {
    const start = offset;
    while (buf[offset] !== 0x0a) offset++;
    const line = buf.toString('ascii', start, offset);
    offset++;
    return line;
  }
  const magic = readLine();
  if (magic.trim() !== 'P6') throw new Error('not a P6 ppm: ' + magic);
  const [w, h] = readLine().trim().split(/\s+/).map(Number);
  readLine();
  const rgb = buf.subarray(offset);
  const n = w * h;
  const rgba = new Uint8ClampedArray(n * 4);
  for (let i = 0; i < n; i++) {
    rgba[i * 4] = rgb[i * 3];
    rgba[i * 4 + 1] = rgb[i * 3 + 1];
    rgba[i * 4 + 2] = rgb[i * 3 + 2];
    rgba[i * 4 + 3] = 255;
  }
  return { data: rgba, width: w, height: h };
}

const groundTruth = JSON.parse(fs.readFileSync(path.join(outDir, 'ground_truth.json'), 'utf-8'));

function absDiff(a, b) {
  if (a === null || b === null) return a === b ? 0 : NaN;
  return Math.abs(a - b);
}

let gradeMismatches = 0;
for (const fname of Object.keys(groundTruth).sort()) {
  const ppmPath = path.join(outDir, 'ppm', fname + '.ppm');
  const img = readPPM(ppmPath);
  const jsFeat = extractFeatures(img);
  const jsPred = predict(jsFeat);
  const gt = groundTruth[fname];
  const pyFeat = gt.extract_features_on_resized_array;
  const pyPred = gt.predict_full;

  const gradeMatch = pyPred.grade === jsPred.grade;
  if (!gradeMatch) gradeMismatches++;

  console.log(`\n=== ${fname} ===`);
  console.log('  python:', JSON.stringify(pyFeat), '->', pyPred.grade, pyPred.confidence?.toFixed(4));
  console.log('  js    :', JSON.stringify(jsFeat), '->', jsPred.grade, jsPred.confidence?.toFixed(4));
  if (pyFeat && jsFeat) {
    console.log(
      '  diff  :',
      JSON.stringify({
        vr_whole: absDiff(pyFeat.vr_whole, jsFeat.vr_whole),
        blob_largest_frac: absDiff(pyFeat.blob_largest_frac, jsFeat.blob_largest_frac),
        blob_n: absDiff(pyFeat.blob_n, jsFeat.blob_n),
        n_px: absDiff(pyFeat.n_px, jsFeat.n_px),
      }),
      gradeMatch ? 'GRADE MATCH' : 'GRADE MISMATCH ***'
    );
  }
}

console.log(`\n\n${gradeMismatches === 0 ? 'ALL GRADES MATCH' : gradeMismatches + ' GRADE MISMATCH(ES)'}`);
