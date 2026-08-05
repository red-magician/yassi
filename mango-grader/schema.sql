-- D1 schema for the mango grader feedback loop.
-- Mirrors the field names mango_grader.py's log_prediction()/record_correction()
-- write to feedback_log/log.jsonl and feedback_log/corrections.jsonl, so
-- /api/export can produce files retrain.py can consume without modification.

CREATE TABLE IF NOT EXISTS predictions (
  log_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  user_id TEXT,
  machine_grade TEXT,
  confidence REAL,
  needs_review INTEGER,
  vr_whole REAL,
  blob_largest_frac REAL,
  blob_n INTEGER,
  note TEXT
);

CREATE TABLE IF NOT EXISTS corrections (
  log_id TEXT PRIMARY KEY REFERENCES predictions(log_id),
  created_at TEXT NOT NULL,
  human_grade TEXT NOT NULL,
  source TEXT NOT NULL,
  has_defect INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);
