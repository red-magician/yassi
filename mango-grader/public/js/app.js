import { A_THR_DEFAULT, H_THR_DEFAULT } from './features.js';
import { t, applyTranslations, getLang, setLang } from './i18n.js';

const $ = (sel) => document.querySelector(sel);

const screens = {
  home: $('#screen-home'),
  loading: $('#screen-loading'),
  result: $('#screen-result'),
  correct: $('#screen-correct'),
  calibrate: $('#screen-calibrate'),
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

// ---- active color thresholds (a_thr/h_thr), overridable via in-app
// calibration; falls back to the model's built-in defaults ----
function getActiveThresholds() {
  const a = localStorage.getItem('mango_a_thr');
  const h = localStorage.getItem('mango_h_thr');
  if (a !== null && h !== null) {
    return { aThr: Number(a), hThr: Number(h), isCustom: true };
  }
  return { aThr: A_THR_DEFAULT, hThr: H_THR_DEFAULT, isCustom: false };
}

function setActiveThresholds(aThr, hThr) {
  localStorage.setItem('mango_a_thr', String(aThr));
  localStorage.setItem('mango_h_thr', String(hThr));
  renderThresholdStatus();
}

function resetActiveThresholds() {
  localStorage.removeItem('mango_a_thr');
  localStorage.removeItem('mango_h_thr');
  renderThresholdStatus();
}

function renderThresholdStatus() {
  const { aThr, hThr, isCustom } = getActiveThresholds();
  $('#threshold-status-text').textContent = t(
    isCustom ? 'calibrate.thresholdCustom' : 'calibrate.thresholdDefault',
    { a: aThr, h: hThr }
  );
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
  const { aThr, hThr } = getActiveThresholds();
  return new Promise((resolve, reject) => {
    pending.set(requestId, { resolve, reject });
    worker.postMessage({ imageData, requestId, aThr, hThr });
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
    alert(t('result.processFailedAlert', { error: err && err.message ? err.message : err }));
  }
}

function renderResult(result) {
  const badge = $('#grade-badge');
  const confEl = $('#confidence-value');
  const reviewEl = $('#needs-review-banner');
  const noteEl = $('#result-note');
  const featEl = $('#feature-details');

  if (result.error) {
    badge.textContent = t('result.gradeUnknown');
    badge.className = 'grade-badge grade-unknown';
    confEl.textContent = '-';
    reviewEl.classList.remove('hidden');
    reviewEl.textContent = '⚠ ' + t('result.error.' + result.error) + t('result.errorHint');
    noteEl.classList.add('hidden');
    featEl.innerHTML = '';
    return;
  }

  badge.textContent = result.grade;
  badge.className = 'grade-badge ' + GRADE_CLASS[result.grade];
  $('#grade-label').textContent = t('result.gradeLabel.' + result.grade);
  confEl.textContent = Math.round(result.confidence * 100) + '%';

  if (result.needs_review) {
    reviewEl.classList.remove('hidden');
    reviewEl.textContent = t('result.needsReview');
  } else {
    reviewEl.classList.add('hidden');
  }

  if (result.note) {
    noteEl.classList.remove('hidden');
    noteEl.textContent = 'ℹ ' + t('result.note.' + result.note);
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
    <dt>${t('result.probaLabel')}</dt><dd>${probaStr}</dd>
    <dt>${t('result.vrWholeLabel')}</dt><dd>${f.vr_whole.toFixed(1)}%</dd>
    <dt>${t('result.blobFracLabel')}</dt><dd>${f.blob_largest_frac.toFixed(1)}%</dd>
    <dt>${t('result.blobNLabel')}</dt><dd>${f.blob_n}</dd>
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
    alert(t('result.correctionSentAlert'));
  } catch (err) {
    alert(t('result.correctionFailedAlert'));
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

// ---- calibration mode ----
const calibrateWorker = new Worker('./js/calibrate-worker.js', { type: 'module' });
let calibrateRequestId = 1;
let calibrationItems = []; // {id, previewUrl, imageData, grade}

function renderCalibrateList() {
  const list = $('#calibrate-list');
  if (calibrationItems.length === 0) {
    list.innerHTML = `<p class="calibrate-empty">${t('calibrate.empty')}</p>`;
  } else {
    list.innerHTML = calibrationItems
      .map(
        (item) => `
        <div class="calibrate-item" data-id="${item.id}">
          <img src="${item.previewUrl}" alt="" />
          <select class="grade-select" data-id="${item.id}">
            <option value="" ${item.grade === '' ? 'selected' : ''}>${t('calibrate.gradeSelectPlaceholder')}</option>
            <option value="A" ${item.grade === 'A' ? 'selected' : ''}>${t('grade.A')}</option>
            <option value="B" ${item.grade === 'B' ? 'selected' : ''}>${t('grade.B')}</option>
            <option value="C" ${item.grade === 'C' ? 'selected' : ''}>${t('grade.C')}</option>
          </select>
          <button type="button" class="remove-btn" data-id="${item.id}">✕</button>
        </div>`
      )
      .join('');
  }
  const graded = calibrationItems.filter((it) => it.grade);
  $('#calibrate-run-btn').disabled = graded.length < 4;
}

$('#calibrate-input').addEventListener('change', async (e) => {
  const files = Array.from(e.target.files || []);
  e.target.value = '';
  for (const file of files) {
    try {
      const { imageData, previewUrl } = await loadFileToImageData(file, MAXPX);
      calibrationItems.push({ id: crypto.randomUUID(), previewUrl, imageData, grade: '' });
    } catch (err) {
      console.warn('写真の読み込みに失敗', err);
    }
  }
  renderCalibrateList();
});

$('#calibrate-list').addEventListener('change', (e) => {
  if (!e.target.classList.contains('grade-select')) return;
  const item = calibrationItems.find((it) => it.id === e.target.dataset.id);
  if (item) item.grade = e.target.value;
  renderCalibrateList();
});

$('#calibrate-list').addEventListener('click', (e) => {
  if (!e.target.classList.contains('remove-btn')) return;
  calibrationItems = calibrationItems.filter((it) => it.id !== e.target.dataset.id);
  renderCalibrateList();
});

$('#open-calibrate-btn').addEventListener('click', () => {
  $('#calibrate-result').classList.add('hidden');
  $('#calibrate-progress').classList.add('hidden');
  renderCalibrateList();
  showScreen('calibrate');
});

$('#calibrate-back-btn').addEventListener('click', () => showScreen('home'));

$('#calibrate-reset-btn').addEventListener('click', () => {
  resetActiveThresholds();
  alert(t('calibrate.resetAlert'));
});

$('#calibrate-run-btn').addEventListener('click', () => {
  const graded = calibrationItems.filter((it) => it.grade);
  if (graded.length < 4) return;

  $('#calibrate-run-btn').disabled = true;
  $('#calibrate-result').classList.add('hidden');
  $('#calibrate-progress').classList.remove('hidden');
  $('#calibrate-progress-text').textContent = t('calibrate.progressDefault');

  const requestId = calibrateRequestId++;
  const { aThr, hThr } = getActiveThresholds();

  const onMessage = (e) => {
    const msg = e.data;
    if (msg.requestId !== requestId) return;
    if (msg.type === 'progress') {
      $('#calibrate-progress-text').textContent = t('calibrate.progressWithCount', {
        done: msg.done,
        total: msg.total,
      });
      return;
    }
    calibrateWorker.removeEventListener('message', onMessage);
    $('#calibrate-progress').classList.add('hidden');
    $('#calibrate-run-btn').disabled = false;
    if (msg.type === 'error') {
      alert(t('calibrate.failedAlert', { error: msg.error }));
      return;
    }
    renderCalibrateResult(msg);
  };
  calibrateWorker.addEventListener('message', onMessage);

  calibrateWorker.postMessage({
    requestId,
    items: graded.map((it) => ({ imageData: it.imageData, humanGrade: it.grade })),
    currentAThr: aThr,
    currentHThr: hThr,
  });
});

let lastCalibrateResultMsg = null;

function renderCalibrateResult(msg) {
  lastCalibrateResultMsg = msg;
  const { best, currentScore, noFruitCount, nPhotos } = msg;
  const { aThr: curA, hThr: curH } = getActiveThresholds();
  const improved = best.score > currentScore + 1e-9;
  const el = $('#calibrate-result');
  el.classList.remove('hidden');
  el.innerHTML = `
    <p>${t('calibrate.resultSummary', { n: nPhotos, noFruit: noFruitCount })}</p>
    <p>${t('calibrate.resultCurrentScore', { a: curA, h: curH, score: currentScore.toFixed(3) })}</p>
    <p>${t('calibrate.resultBestScore', { a: best.aThr, h: best.hThr, score: best.score.toFixed(3) })}</p>
    <p class="${improved ? 'improved' : 'not-improved'}">
      ${improved ? t('calibrate.resultImproved') : t('calibrate.resultNotImproved')}
    </p>
    <button type="button" id="calibrate-apply-btn" class="btn btn-primary">${t('calibrate.apply')}</button>
  `;
  $('#calibrate-apply-btn').addEventListener('click', () => {
    setActiveThresholds(best.aThr, best.hThr);
    alert(t('calibrate.applyAlert', { a: best.aThr, h: best.hThr }));
  });
}

// ---- language switcher ----
const langSelect = $('#lang-select');
langSelect.value = getLang();
langSelect.addEventListener('change', () => {
  setLang(langSelect.value); // re-applies data-i18n text automatically
  renderThresholdStatus();
  renderCalibrateList();
  if (lastCalibrateResultMsg) renderCalibrateResult(lastCalibrateResultMsg);
  if (lastResult) renderResult(lastResult);
});

// service worker (offline / installable)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch((err) => console.warn('SW登録失敗', err));
  });
}

applyTranslations();
renderThresholdStatus();
showScreen('home');
