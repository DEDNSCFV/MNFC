-- 001_initial — baseline del schema MNFC
-- Refleja schema_limpio.sql. Primera migración aplicable.
-- SQLite: no usa IF NOT EXISTS en índices porque ya lo hace por PK.

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- El schema real ya está en schema_limpio.sql (aplicado por ingest_txt)
-- Esta migración solo registra el baseline.
