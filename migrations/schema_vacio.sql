-- ESQUEMA MNFC v0.5.0 (Base de Datos Vacía)
-- Generado automáticamente para despliegue en cliente

CREATE TABLE stock_por_sucursal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sucursal TEXT NOT NULL,
            sku TEXT NOT NULL,
            descripcion TEXT,
            almacen TEXT,
            stock REAL,
            UNIQUE(sucursal, sku, almacen)
        );

CREATE TABLE inventario_nodo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        cantidad_fisica INTEGER NOT NULL,
        costo_unitario_cent INTEGER NOT NULL,
        precio_venta_cent INTEGER NOT NULL,
        marca TEXT,
        familia TEXT,
        ultima_actualizacion TEXT NOT NULL
    );

CREATE TABLE hallazgos_auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tipo TEXT NOT NULL,
            severidad TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            evidencia_json TEXT,
            estado TEXT DEFAULT 'REGISTRADO'
        );

CREATE TABLE movimientos_dartony (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT NOT NULL,
        descripcion TEXT,
        tipo TEXT,
        fecha TEXT,
        almacen TEXT,
        cantidad REAL,
        stock_actual REAL,
        costo_unitario_cent INTEGER,
        nodo TEXT,
        numero_documento TEXT
    );

