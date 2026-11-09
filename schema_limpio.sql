CREATE TABLE event_store(
  id INT,
  event_id TEXT,
  tipo_evento TEXT,
  timestamp INT,
  payload TEXT,
  version_contexto TEXT,
  correlation_id TEXT,
  idempotency_key TEXT,
  hash_previo TEXT,
  hash_actual TEXT
);
CREATE TABLE conteo_fisico(
  id INT,
  empresa TEXT,
  sku TEXT,
  descripcion TEXT,
  cantidad_fisica REAL,
  fecha_conteo TEXT,
  archivo_origen TEXT
);
CREATE TABLE politica_costeo(
  id INT,
  sku TEXT,
  metodo TEXT,
  justificacion TEXT,
  fecha_desde TEXT,
  fecha_hasta TEXT,
  autor TEXT,
  estado TEXT
);
CREATE VIEW v_movimientos_centimos AS
SELECT
  id,
  json_extract(payload, '$.sku') AS sku,
  json_extract(payload, '$.nodo') AS nodo,
  json_extract(payload, '$.almacen') AS almacen,
  json_extract(payload, '$.fecha') AS fecha,
  json_extract(payload, '$.tipo') AS tipo,
  json_extract(payload, '$.renglon') AS renglon,
  CAST(ROUND(CAST(json_extract(payload,'$.entradas') AS REAL) * 100) AS INTEGER) AS entradas_cent,
  CAST(ROUND(CAST(json_extract(payload,'$.salidas')  AS REAL) * 100) AS INTEGER) AS salidas_cent,
  CAST(ROUND(CAST(json_extract(payload,'$.stock_actual') AS REAL) * 100) AS INTEGER) AS stock_cent,
  CAST(ROUND(CAST(json_extract(payload,'$.costo_unitario') AS REAL) * 100) AS INTEGER) AS costo_cent
FROM event_store
WHERE tipo_evento = 'ASIENTO_INGERIDO'
/* v_movimientos_centimos(id,sku,nodo,almacen,fecha,tipo,renglon,entradas_cent,salidas_cent,stock_cent,costo_cent) */;
CREATE TABLE ciclo_diario (
  id INTEGER PRIMARY KEY,
  fecha TEXT,
  detal TEXT,
  am1_recibido INTEGER,     -- 1 si, 0 no
  conteo_recibido INTEGER,  -- 1 si, 0 no
  am2_recibido INTEGER,     -- 1 si, 0 no
  estado TEXT CHECK(estado IN ('COMPLETO', 'PARCIAL', 'CERRADO')),
  observacion TEXT          -- Ej: "Palo Verde no entregó AM2"
);
CREATE TABLE acta_marco (
  id INTEGER PRIMARY KEY,
  version TEXT,             -- 'v1.0'
  materialidad_centimos INTEGER DEFAULT 50, -- Los $0.50 de M2
  regla_sin_ajus TEXT,      -- 'NO_DETERMINADA' (M3)
  firma_auditor TEXT,       -- Tu CPC 183594
  firma_gerencia TEXT,      -- Nombre del gerente
  hash_acta TEXT,           -- SHA256 del acuerdo
  fecha_firma TEXT
);
CREATE TABLE decision (
  id INTEGER PRIMARY KEY,
  sku TEXT NOT NULL,
  detal TEXT NOT NULL,
  hallazgo TEXT,
  decision_tomada TEXT CHECK(decision_tomada IN ('APLICAR','RECHAZAR','DIFERIR','ESCALAR')),
  justificacion TEXT NOT NULL,
  residuo TEXT,             -- Qué no se pudo resolver
  autor TEXT NOT NULL,      -- Tu nombre
  cpc TEXT NOT NULL,        -- '183594'
  fecha TEXT,
  hash_firma TEXT,          -- SHA256 de la decisión
  aplicado_en_profit INTEGER DEFAULT 0
);
CREATE TABLE hallazgo_extra (
  id INTEGER PRIMARY KEY,
  fecha TEXT,
  detal TEXT,
  sku TEXT,
  tipo_hallazgo TEXT, -- 'AUDITORIA_FISICA', 'OBSERVACION_ENCARGADO', 'ANOMALIA_SISTEMA', 'SOSPECHA_FRAUDE'
  descripcion TEXT NOT NULL, -- Lo que encontraste (ej: "Batería dañada MO-009 en anaquel")
  impacto_estimado_centimos INTEGER, -- En céntimos, siempre
  requiere_ajuste INTEGER DEFAULT 0, -- 1 si necesita ajuste en Profit
  estado TEXT CHECK(estado IN ('DETECTADO', 'EN_VERIFICACION', 'RESUELTO', 'ESCALADO')),
  evidencia_hash TEXT, -- SHA256 de la foto o el documento
  autor TEXT, -- Quién lo encontró (tú o el encargado)
  fecha_registro TEXT
);
CREATE TABLE grafo_nodos (
  id INTEGER PRIMARY KEY,
  tipo TEXT NOT NULL,      -- 'SKU', 'MOVIMIENTO', 'HALLAZGO', 'DECISION', 'NORMA'
  nombre TEXT NOT NULL,    -- '2333', 'MO-017', 'NIC 2', 'FIFO'
  contenido TEXT,          -- Datos extra (JSON o texto)
  hash TEXT                -- SHA256 del nodo
);
CREATE TABLE grafo_aristas (
  id INTEGER PRIMARY KEY,
  origen_id INTEGER,       -- Nodo de donde sale la flecha
  destino_id INTEGER,      -- Nodo a donde llega la flecha
  relacion TEXT,           -- 'TIENE_MOVIMIENTO', 'GENERA_HALLAZGO', 'SE_RESUELVE_CON', 'VIOLA_NORMA'
  peso REAL,               -- Opcional: para dar grosor a la línea (ej. impacto en $)
  fecha TEXT,
  FOREIGN KEY(origen_id) REFERENCES grafo_nodos(id),
  FOREIGN KEY(destino_id) REFERENCES grafo_nodos(id)
);
CREATE TABLE firma_auditor (
  id INTEGER PRIMARY KEY,
  decision_id INTEGER,
  cpc TEXT NOT NULL,
  nombre TEXT NOT NULL,
  datos_firmados TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  hash_anterior TEXT,
  hash_firma TEXT UNIQUE
);
CREATE TABLE auditoria_compras (
  id INTEGER PRIMARY KEY,
  fecha TEXT,
  proveedor TEXT,
  numero_factura TEXT,
  monto_centimos INTEGER,
  recibido_en_almacen INTEGER, -- 1 si, 0 no
  estado TEXT CHECK(estado IN ('CUADRADO', 'FALTANTE', 'SOBRANTE', 'DEVUELTO')),
  decision_auditor TEXT,
  firma_auditor TEXT
);
CREATE TABLE auditoria_ventas (
  id INTEGER PRIMARY KEY,
  fecha TEXT,
  cliente TEXT,
  numero_factura TEXT,
  monto_centimos INTEGER,
  despachado_en_almacen INTEGER, -- 1 si, 0 no
  estado TEXT CHECK(estado IN ('CUADRADO', 'PENDIENTE_DESPACHO', 'ANULADO')),
  decision_auditor TEXT,
  firma_auditor TEXT
);
CREATE VIEW v_leccion_aprendida AS
SELECT 
    c.sku,
    c.descripcion,
    c.cantidad_fisica AS 'Lo_que_hay_en_anaquel',
    (SELECT stock_cent/100.0 FROM v_movimientos_centimos v WHERE v.sku = c.sku ORDER BY v.id DESC LIMIT 1) AS 'Lo_que_dice_el_sistema',
    (c.cantidad_fisica - (SELECT stock_cent/100.0 FROM v_movimientos_centimos v WHERE v.sku = c.sku ORDER BY v.id DESC LIMIT 1)) AS 'Diferencia',
    CASE 
        WHEN (c.cantidad_fisica - (SELECT stock_cent/100.0 FROM v_movimientos_centimos v WHERE v.sku = c.sku ORDER BY v.id DESC LIMIT 1)) < 0 
        THEN '⚠️ FALTANTE: Revisar NIA 501. Posible error de despacho o robo.'
        WHEN (c.cantidad_fisica - (SELECT stock_cent/100.0 FROM v_movimientos_centimos v WHERE v.sku = c.sku ORDER BY v.id DESC LIMIT 1)) > 0 
        THEN '⚠️ SOBRANTE: Revisar NIIF 2. Posible error de recepción de factura.'
        ELSE '✅ CUADRADO: El anaquel y el sistema coinciden.'
    END AS 'Leccion_que_debes_aprender'
FROM conteo_fisico c
WHERE c.cantidad_fisica > 0
/* v_leccion_aprendida(sku,descripcion,Lo_que_hay_en_anaquel,Lo_que_dice_el_sistema,Diferencia,Leccion_que_debes_aprender) */;
