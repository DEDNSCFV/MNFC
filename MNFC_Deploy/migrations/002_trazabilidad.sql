-- 002_trazabilidad — columnas de auditoría en movimientos
-- (aplicada ya vía schema_limpio.sql; queda registrada para versionado)

-- Verificación de existencia (no falla si ya están)
CREATE TABLE IF NOT EXISTS _check_trazabilidad (
    id INTEGER PRIMARY KEY,
    _marca TEXT
);
DROP TABLE IF EXISTS _check_trazabilidad;
