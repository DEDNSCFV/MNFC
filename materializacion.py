#!/usr/bin/env python3
"""
materializacion.py
Decorador y utilidades para el seguimiento de hora en cada materialización.
Rodríguez: "la mano deja huella temporal".
"""

import functools
import hashlib
import sqlite3
import time
from datetime import datetime
from pathlib import Path

DB = "/data/data/com.termux/files/home/MNFC/nodo_principal_dartony.db"


def crear_tabla():
    """Crea la tabla materializaciones si no existe."""
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS materializaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        materializacion_id TEXT UNIQUE NOT NULL,
        tipo TEXT NOT NULL,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        hito_asociado TEXT,
        ciclo INTEGER,
        operador TEXT NOT NULL,
        hora_inicio TEXT NOT NULL,
        hora_fin TEXT NOT NULL,
        duracion_segundos INTEGER,
        hash_artefacto TEXT,
        archivo_resultado TEXT,
        notas TEXT,
        es_retroactiva INTEGER DEFAULT 0,
        fecha_original TEXT,
        creado_en TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_mat_tipo ON materializaciones(tipo);
    CREATE INDEX IF NOT EXISTS idx_mat_hito ON materializaciones(hito_asociado);
    CREATE INDEX IF NOT EXISTS idx_mat_ciclo ON materializaciones(ciclo);
    CREATE INDEX IF NOT EXISTS idx_mat_operador ON materializaciones(operador);
    CREATE INDEX IF NOT EXISTS idx_mat_fecha ON materializaciones(hora_inicio);
    """)
    con.commit()
    con.close()


def materializacion(tipo, nombre, hito=None, ciclo=4,
                    operador="Domingo E. Díaz N. (C.P.C. 183594)"):
    """
    Decorador que registra cada materialización con:
    - hora de inicio
    - hora de fin
    - duración en segundos
    - hash del resultado
    - operador
    - hito asociado
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            hora_inicio = datetime.now()
            resultado = func(*args, **kwargs)
            hora_fin = datetime.now()
            duracion = int((hora_fin - hora_inicio).total_seconds())

            # Hash del resultado
            try:
                hash_resultado = hashlib.sha256(str(resultado).encode()).hexdigest()[:32]
            except Exception:
                hash_resultado = None

            # Registrar en BD
            mat_id = f"MAT-{hora_inicio.strftime('%Y-%m-%d')}-{int(time.time()) % 10000:04d}"
            con = sqlite3.connect(DB)
            con.execute("""
                INSERT OR IGNORE INTO materializaciones
                (materializacion_id, tipo, nombre, hito_asociado, ciclo,
                 operador, hora_inicio, hora_fin, duracion_segundos,
                 hash_artefacto, archivo_resultado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mat_id, tipo, nombre, hito, ciclo, operador,
                hora_inicio.isoformat(), hora_fin.isoformat(), duracion,
                hash_resultado, None,
            ))
            con.commit()
            con.close()

            print(f"\n  [MATERIALIZACION REGISTRADA]")
            print(f"  ID:        {mat_id}")
            print(f"  Tipo:      {tipo} — {nombre}")
            print(f"  Inicio:    {hora_inicio.strftime('%H:%M:%S')}")
            print(f"  Fin:       {hora_fin.strftime('%H:%M:%S')}")
            print(f"  Duracion:  {duracion}s")
            if hash_resultado:
                print(f"  Hash:      {hash_resultado}")
            print()

            return resultado
        return wrapper
    return decorator


def resumen_materializaciones(ciclo=4):
    """Sinopsis de materializaciones del ciclo."""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    print("=" * 78)
    print(f"SINOPSIS DE MATERIALIZACIONES — CICLO {ciclo}")
    print("=" * 78)
    print()

    total = con.execute(
        "SELECT COUNT(*) FROM materializaciones WHERE ciclo=?", (ciclo,)
    ).fetchone()[0]
    total_seg = con.execute(
        "SELECT COALESCE(SUM(duracion_segundos), 0) FROM materializaciones WHERE ciclo=?",
        (ciclo,)
    ).fetchone()[0]

    print(f"  Materializaciones: {total}")
    print(f"  Tiempo total: {total_seg // 3600}h {(total_seg % 3600) // 60}m {total_seg % 60}s")
    print()

    print(f"  {'Hora inicio':12s} {'Hora fin':12s} {'Dur':>6s} {'Tipo':12s} {'Nombre':30s}")
    print(f"  {'-'*12} {'-'*12} {'-'*6} {'-'*12} {'-'*30}")
    for r in con.execute("""
        SELECT hora_inicio, hora_fin, duracion_segundos, tipo, nombre
        FROM materializaciones
        WHERE ciclo = ?
        ORDER BY hora_inicio
    """, (ciclo,)):
        hi = r['hora_inicio'][11:19] if len(r['hora_inicio']) > 11 else r['hora_inicio']
        hf = r['hora_fin'][11:19] if len(r['hora_fin']) > 11 else r['hora_fin']
        dur = f"{r['duracion_segundos']}s"
        print(f"  {hi:12s} {hf:12s} {dur:>6s} {r['tipo']:12s} {r['nombre'][:30]:30s}")

    print()
    con.close()
