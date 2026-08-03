// POST /api/log — records a machine prediction (features + grade, never the
// photo itself). Mirrors mango_grader.py's log_prediction().
export async function onRequestPost({ request, env }) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'invalid json' }, 400);
  }

  const logId = typeof body.log_id === 'string' ? body.log_id.slice(0, 64) : null;
  if (!logId) return json({ error: 'log_id is required' }, 400);

  const grade = ['A', 'B', 'C'].includes(body.machine_grade) ? body.machine_grade : null;
  const confidence = Number.isFinite(body.confidence) ? body.confidence : null;
  const needsReview = body.needs_review ? 1 : 0;
  const features = body.features && typeof body.features === 'object' ? body.features : {};
  const userId = typeof body.user_id === 'string' ? body.user_id.slice(0, 64) : null;
  const note = typeof body.note === 'string' ? body.note.slice(0, 500) : null;

  await env.DB.prepare(
    `INSERT INTO predictions
       (log_id, created_at, user_id, machine_grade, confidence, needs_review, vr_whole, blob_largest_frac, blob_n, note)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)
     ON CONFLICT(log_id) DO NOTHING`
  )
    .bind(
      logId,
      new Date().toISOString(),
      userId,
      grade,
      confidence,
      needsReview,
      numOrNull(features.vr_whole),
      numOrNull(features.blob_largest_frac),
      numOrNull(features.blob_n),
      note
    )
    .run();

  return json({ ok: true, log_id: logId });
}

function numOrNull(v) {
  return Number.isFinite(v) ? v : null;
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
}
