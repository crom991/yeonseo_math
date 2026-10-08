CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  edit_token_hash TEXT NOT NULL,
  completed_at TEXT NOT NULL,
  local_date TEXT NOT NULL,
  domain TEXT NOT NULL,
  start_level INTEGER NOT NULL,
  final_level INTEGER NOT NULL,
  recommended_level INTEGER NOT NULL,
  attempted INTEGER NOT NULL,
  correct INTEGER NOT NULL,
  accuracy REAL NOT NULL,
  elapsed_seconds INTEGER NOT NULL,
  feeling TEXT NOT NULL DEFAULT '',
  telegram_sent_at TEXT,
  records_json TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_sessions_completed_at ON sessions(completed_at);
CREATE INDEX IF NOT EXISTS idx_sessions_domain ON sessions(domain, completed_at);

CREATE TABLE IF NOT EXISTS settings (
  id TEXT PRIMARY KEY,
  settings_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
