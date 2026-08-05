// POST /api/correction — records a human correction for a prior prediction.
// Mirrors mango_grader.py's record_correction(). This is what makes a
// logged prediction usable for retraining (unconfirmed predictions are
// never trained on, matching retrain.py's rule).
export async function onRequestPost({ request, env }) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'invalid json' }, 400);
  }

  const logId = typeof body.log_id === 'string' ? body.log_id.slice(0, 64) : null;
  const humanGrade = body.human_grade;
  if (!logId) return json({ error: 'log_id is required' }, 400);
  if (!['A', 'B', 'C'].includes(humanGrade)) return json({ error: 'human_grade must be A, B or C' }, 400);

  const source = typeof body.source === 'string' ? body.source.slice(0, 32) : 'app_user';
  const hasDefect = body.has_defect ? 1 : 0;

  await env.DB.prepare(
    `INSERT INTO corrections (log_id, created_at, human_grade, source, has_defect)
     VALUES (?1, ?2, ?3, ?4, ?5)
     ON CONFLICT(log_id) DO UPDATE SET
       created_at = excluded.created_at,
       human_grade = excluded.human_grade,
       source = excluded.source,
       has_defect = excluded.has_defect`
  )
    .bind(logId, new Date().toISOString(), humanGrade, source, hasDefect)
    .run();

  return json({ ok: true });
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
}
