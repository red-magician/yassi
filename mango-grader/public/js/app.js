const $ = (sel) => document.querySelector(sel);

const screens = {
  home: $('#screen-home'),
  loading: $('#screen-loading'),
  result: $('#screen-result'),
  correct: $('#screen-correct'),
};

function showScreen(name) {
  for (const key in screens) screens[key].classList.toggle('hidden', key !== name);
}

// ---- persistent anonymous device id (for grouping corrections only; no
// personal info, never leaves the device except as this opaque string) ----
function getUserId() {
  let id = localStorage.getItem('mango_user_id');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('mango_user_id', id);
  }
  return id;
}

function sendEnabled() {
  return localStorage.getItem('mango_send_logs') !== 'off';
}

// ---- worker plumbing ----
const worker = new Worker('./js/worker.js', { type: 'module' });
let nextRequestId = 1;
const pending = new Map();
worker.onmessage = (e) => {
  const { requestId, ok, result, error } = e.data;
  const cb = pending.get(requestId);
  if (!cb) return;
  pending.delete(requestId);
  ok ? cb.resolve(result) : cb.reject(new Error(error));
};

function runPipeline(imageData) {
  const requestId = nextRequestId++;
  return new Promise((resolve, reject) => {
    pending.set(requestId, { resolve, reject });
    worker.postMessage({ imageData, requestId });
  });
}

// ---- image loading (EXIF-aware) + downscale to MAXPX, matching the
// Python reference's PIL resize before feature extraction ----
const MAXPX = 1200;

async function loadFileToImageData(file, maxPx) {
  let bitmap;
  if ('createImageBitmap' in window) {
    bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
  } else {
    bitmap = await loadImageElementFallback(file);
  }
  const scale = Math.min(1, maxPx / Math.max(bitmap.width, bitmap.height));
  const w = Math.max(1, Math.round(bitmap.width * scale));
  const h = Math.max(1, Math.round(bitmap.height * scale));
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(bitmap, 0, 0, w, h);
  const imageData = ctx.getImageData(0, 0, w, h);
  const previewUrl = canvas.toDataURL('image/jpeg', 0.85);
  if (bitmap.close) bitmap.close();
  return { imageData, previewUrl };
}

function loadImageElementFallback(file) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = (err) => {
      URL.revokeObjectURL(url);
      reject(err);
    };
    img.src = url;
  });
}

// ---- grade presentation ----
const GRADE_LABEL = { A: '赤秀 A', B: '黒秀 B', C: '白箱 C' };
const GRADE_CLASS = { A: 'grade-a', B: 'grade-b', C: 'grade-c' };

let lastResult = null;
let lastLogId = null;

async function handleFile(file) {
  if (!file) return;
  showScreen('loading');
  try {
    const { imageData, previewUrl } = await loadFileToImageData(file, MAXPX);
    $('#result-preview').src = previewUrl;
    const result = await runPipeline(imageData);
    lastResult = result;
    renderResult(result);
    await logPrediction(result);
    showScreen('result');
  } catch (err) {
    console.error(err);
    showScreen('home');
    alert('画像の処理に失敗しました: ' + (err && err.message ? err.message : err));
  }
}

function renderResult(result) {
  const badge = $('#grade-badge');
  const confEl = $('#confidence-value');
  const reviewEl = $('#needs-review-banner');
  const noteEl = $('#result-note');
  const featEl = $('#feature-details');

  if (result.error) {
    badge.textContent = '？';
    badge.className = 'grade-badge grade-unknown';
    confEl.textContent = '-';
    reviewEl.classList.remove('hidden');
    reviewEl.textContent = '⚠ ' + result.error + '（背景や写り方を変えて再撮影してください）';
    noteEl.classList.add('hidden');
    featEl.innerHTML = '';
    return;
  }

  badge.textContent = result.grade;
  badge.className = 'grade-badge ' + GRADE_CLASS[result.grade];
  $('#grade-label').textContent = GRADE_LABEL[result.grade];
  confEl.textContent = Math.round(result.confidence * 100) + '%';

  if (result.needs_review) {
    reviewEl.classList.remove('hidden');
    reviewEl.textContent = '⚠ 確信度が低い判定です。人の目で確認してください。';
  } else {
    reviewEl.classList.add('hidden');
  }

  if (result.note) {
    noteEl.classList.remove('hidden');
    noteEl.textContent = 'ℹ ' + result.note;
  } else {
    noteEl.classList.add('hidden');
  }

  const f = result.features;
  const probaStr = result.proba
    ? Object.entries(result.proba)
        .map(([g, p]) => `${g}: ${Math.round(p * 100)}%`)
        .join(' / ')
    : '-';
  featEl.innerHTML = `
    <dt>確率内訳</dt><dd>${probaStr}</dd>
    <dt>鮮紅色の面積割合 (vr_whole)</dt><dd>${f.vr_whole.toFixed(1)}%</dd>
    <dt>最大連結成分の割合 (blob_largest_frac)</dt><dd>${f.blob_largest_frac.toFixed(1)}%</dd>
    <dt>連結成分の数 (blob_n)</dt><dd>${f.blob_n}</dd>
  `;
}

async function logPrediction(result) {
  lastLogId = crypto.randomUUID().replace(/-/g, '').slice(0, 12);
  if (!sendEnabled()) return;
  try {
    await fetch('/api/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        log_id: lastLogId,
        user_id: getUserId(),
        machine_grade: result.grade,
        confidence: result.confidence,
        needs_review: !!result.needs_review,
        features: result.features,
        note: result.note || result.error || null,
      }),
    });
  } catch (err) {
    console.warn('log送信に失敗（オフラインの可能性）', err);
  }
}

async function submitCorrection(humanGrade, hasDefect) {
  if (!lastLogId) return;
  try {
    await fetch('/api/correction', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        log_id: lastLogId,
        human_grade: humanGrade,
        source: 'app_user',
        has_defect: !!hasDefect,
      }),
    });
    alert('訂正を送信しました。ありがとうございます。');
  } catch (err) {
    alert('送信に失敗しました（オフラインの可能性があります）。');
  }
  showScreen('result');
}

// ---- wiring ----
$('#camera-input').addEventListener('change', (e) => handleFile(e.target.files[0]));
$('#gallery-input').addEventListener('change', (e) => handleFile(e.target.files[0]));
$('#retake-btn').addEventListener('click', () => showScreen('home'));
$('#wrong-btn').addEventListener('click', () => showScreen('correct'));
$('#correct-cancel-btn').addEventListener('click', () => showScreen('result'));
$('#correct-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const grade = new FormData(e.target).get('human_grade');
  const hasDefect = $('#has-defect').checked;
  if (!grade) return;
  submitCorrection(grade, hasDefect);
});

const sendToggle = $('#send-logs-toggle');
sendToggle.checked = sendEnabled();
sendToggle.addEventListener('change', () => {
  localStorage.setItem('mango_send_logs', sendToggle.checked ? 'on' : 'off');
});

// service worker (offline / installable)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch((err) => console.warn('SW登録失敗', err));
  });
}

showScreen('home');
