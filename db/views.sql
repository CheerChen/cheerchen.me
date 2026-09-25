-- Schema for the D1 database bound to the Pages project as VIEWS_DB.
-- Apply with: wrangler d1 execute cheerchen-me-views --remote --file=db/views.sql
CREATE TABLE IF NOT EXISTS views (
  key        TEXT PRIMARY KEY,           -- post bundle directory, e.g. "posts/foo"
  count      INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
