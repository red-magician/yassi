// GET /api/export?token=...&kind=log|corrections|summary
//
// Exports feedback data in the exact schema mango_grader.py's
// log_prediction()/record_correction() write locally, so the files can be
// dropped straight into feedback_log/ next to retrain.py and it just works
// (retrain.py only touches rec["image_file"] when a log entry has no
// "features", and every entry logged by this app always has features, so
// no photos ever need to leave the device for retraining).
//
// Gated by an EXPORT_TOKEN secret (wrangler secret put EXPORT_TOKEN).
// Refuses to serve anything if that secret isn't configured.
export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const token = url.searchParams.get('token');
  if (!env.EXPORT_TOKEN || token !== env.EXPORT_TOKEN) {
    return json({ error: 'unauthorized' }, 401);
  }

  const kind = url.searchParams.get('kind') || 'summary';

  if (kind === 'log') {
    const { results } = await env.DB.prepare('SELECT * FROM predictions ORDER BY created_at').all();
    const lines = results.map((r) =>
      JSON.stringify({
        log_id: r.log_id,
        timestamp: r.created_at,
        user_id: r.user_id,
        image_file: null,
        machine_grade: r.machine_grade,
        confidence: r.confidence,
        needs_review: !!r.needs_review,
        features: { vr_whole: r.vr_whole, blob_largest_frac: r.blob_largest_frac, blob_n: r.blob_n },
        human_grade: null,
        human_grade_source: null,
        extra: {},
      })
    );
    return text(lines.join('\n') + (lines.length ? '\n' : ''), 'log.jsonl');
  }

  if (kind === 'corrections') {
    const { results } = await env.DB.prepare('SELECT * FROM corrections ORDER BY created_at').all();
    const lines = results.map((r) =>
      JSON.stringify({
        log_id: r.log_id,
        timestamp: r.created_at,
        correction_for: r.log_id,
        human_grade: r.human_grade,
        human_grade_source: r.source,
        has_defect: !!r.has_defect,
      })
    );
    return text(lines.join('\n') + (lines.length ? '\n' : ''), 'corrections.jsonl');
  }

  const predCount = await env.DB.prepare('SELECT COUNT(*) AS n FROM predictions').first();
  const corrCount = await env.DB.prepare('SELECT COUNT(*) AS n FROM corrections').first();
  const byGrade = await env.DB.prepare(
    'SELECT human_grade, COUNT(*) AS n FROM corrections GROUP BY human_grade'
  ).all();
  return json({
    predictions: predCount.n,
    corrections: corrCount.n,
    corrections_by_grade: Object.fromEntries(byGrade.results.map((r) => [r.human_grade, r.n])),
    download: {
      log: `/api/export?token=${token}&kind=log`,
      corrections: `/api/export?token=${token}&kind=corrections`,
    },
  });
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), { status, headers: { 'Content-Type': 'application/json' } });
}

function text(body, filename) {
  return new Response(body, {
    status: 200,
    headers: {
      'Content-Type': 'application/x-ndjson; charset=utf-8',
      'Content-Disposition': `attachment; filename="${filename}"`,
    },
  });
}
