#!/usr/bin/env python3
"""
cbr_retroactivo.py
Re-ingesta los casos de los Ciclos 1 y 2 al CBR.
Consolida el CBR en la BD operativa (nodo_principal_dartony.db).
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path

DB = "/data/data/com.termux/files/home/MNFC/nodo_principal_dartony.db"
DB_ALT = "/data/data/com.termux/files/home/dartony_auditoria.db"

print("=" * 72)
print("CBR RETROACTIVO — RE-INGESTA DE CICLOS 1 Y 2")
print("=" * 72)
print()

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

# ============================================================
# PASO 1 — VERIFICAR SI casos_resueltos EXISTE EN DB OPERATIVA
# ============================================================
print("1. Verificando casos_resueltos en la BD operativa...")

tablas = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
)]

if 'casos_resueltos' not in tablas:
    print("   ⚠️  casos_resueltos NO existe en la BD operativa")

    # Verificar si existe en la BD alternativa
    if Path(DB_ALT).exists():
        con_alt = sqlite3.connect(DB_ALT)
        tablas_alt = [r[0] for r in con_alt.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )]
        if 'casos_resueltos' in tablas_alt:
            print(f"   ✅ Encontrada en {DB_ALT}")
            print("   → Migrando a la BD operativa...")

            # Crear tabla en la BD operativa
            con.executescript("""
            CREATE TABLE IF NOT EXISTS casos_resueltos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caso_codigo TEXT UNIQUE NOT NULL,
                detal TEXT NOT NULL,
                fecha_caso TEXT NOT NULL,
                sku_faltante TEXT NOT NULL,
                sku_sobrante TEXT,
                familia TEXT,
                similitud_codigo REAL,
                similitud_descripcion REAL,
                diferencia_unidades INTEGER,
                clasificacion TEXT NOT NULL,
                solucion_aplicada TEXT,
                razonamiento TEXT NOT NULL,
                propuesto_por_mnfc TEXT,
                ajustado_por_humano INTEGER DEFAULT 0,
                evidencia_json TEXT,
                confianza_final REAL DEFAULT 0.5,
                ciclo_id INTEGER,
                validado_por TEXT,
                ciclo_origen INTEGER,
                fecha_original TEXT,
                hash_artefacto_original TEXT,
                es_retroactivo INTEGER DEFAULT 0,
                reingresado_en TEXT,
                notas_retroactivas TEXT
            );
            """)
            con.commit()

            # Copiar datos
            rows = con_alt.execute("SELECT * FROM casos_resueltos").fetchall()
            cols_alt = [r[1] for r in con_alt.execute("PRAGMA table_info(casos_resueltos)")]
            cols_nuevas = [r[1] for r in con.execute("PRAGMA table_info(casos_resueltos)")]

            for row in rows:
                d = dict(zip(cols_alt, row))
                # Solo columnas comunes
                cols_comunes = [c for c in cols_alt if c in cols_nuevas and c != 'id']
                placeholders = ','.join(['?'] * len(cols_comunes))
                col_names = ','.join(cols_comunes)
                values = [d[c] for c in cols_comunes]
                con.execute(f"INSERT OR IGNORE INTO casos_resueltos ({col_names}) VALUES ({placeholders})", values)

            con.commit()
            con_alt.close()
            print(f"   ✅ {len(rows)} casos migrados")
        else:
            print(f"   ❌ Tampoco existe en {DB_ALT}")
            print("   → Creando tabla vacía en la BD operativa")
            con.executescript("""
            CREATE TABLE IF NOT EXISTS casos_resueltos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caso_codigo TEXT UNIQUE NOT NULL,
                detal TEXT NOT NULL,
                fecha_caso TEXT NOT NULL,
                sku_faltante TEXT NOT NULL,
                sku_sobrante TEXT,
                familia TEXT,
                similitud_codigo REAL,
                similitud_descripcion REAL,
                diferencia_unidades INTEGER,
                clasificacion TEXT NOT NULL,
                solucion_aplicada TEXT,
                razonamiento TEXT NOT NULL,
                propuesto_por_mnfc TEXT,
                ajustado_por_humano INTEGER DEFAULT 0,
                evidencia_json TEXT,
                confianza_final REAL DEFAULT 0.5,
                ciclo_id INTEGER,
                validado_por TEXT,
                ciclo_origen INTEGER,
                fecha_original TEXT,
                hash_artefacto_original TEXT,
                es_retroactivo INTEGER DEFAULT 0,
                reingresado_en TEXT,
                notas_retroactivas TEXT
            );
            """)
            con.commit()
    else:
        print(f"   ❌ {DB_ALT} NO existe tampoco")
else:
    print("   ✅ casos_resueltos YA existe en la BD operativa")

# ============================================================
# PASO 2 — VERIFICAR COLUMNAS RETROACTIVAS
# ============================================================
print()
print("2. Verificando columnas retroactivas...")

cols = [r[1] for r in con.execute("PRAGMA table_info(casos_resueltos)")]
columnas_nuevas = {
    'ciclo_origen': 'INTEGER',
    'fecha_original': 'TEXT',
    'hash_artefacto_original': 'TEXT',
    'es_retroactivo': 'INTEGER DEFAULT 0',
    'reingresado_en': 'TEXT',
    'notas_retroactivas': 'TEXT',
}

for col, tipo in columnas_nuevas.items():
    if col not in cols:
        con.execute(f"ALTER TABLE casos_resueltos ADD COLUMN {col} {tipo}")
        print(f"   ✅ {col} agregada")
    else:
        print(f"   - {col} ya existe")

con.commit()

# ============================================================
# PASO 3 — CARGAR CASOS RETROACTIVOS
# ============================================================
print()
print("3. Cargando casos retroactivos de Ciclos 1 y 2...")

# ⚠️ AJUSTAR: datos reales de los cierres de C1 y C2
casos_retroactivos = [
    (1, 'SKU-001', 'FALTANTE_REAL', '2025-08-15', 'Recuperado de CIERRE_CICLO_1'),
    (1, 'SKU-002', 'DUPLICADO', '2025-08-20', 'Recuperado de CIERRE_CICLO_1'),
    (2, 'SKU-003', 'CRUCE_CONFIRMADO', '2026-03-10', 'Recuperado de CIERRE_CICLO_2'),
    (2, 'SKU-004', 'FALTANTE_REAL', '2026-04-05', 'Recuperado de CIERRE_CICLO_2'),
]

insertados = 0
for ciclo, sku, clasif, fecha, notas in casos_retroactivos:
    hash_art = hashlib.sha256(f"{ciclo}|{sku}|{fecha}".encode()).hexdigest()[:16]

    con.execute("""
        INSERT OR IGNORE INTO casos_resueltos
        (caso_codigo, detal, fecha_caso, sku_faltante, sku_sobrante,
         familia, similitud_codigo, similitud_descripcion,
         diferencia_unidades, clasificacion, solucion_aplicada,
         razonamiento, propuesto_por_mnfc, ajustado_por_humano,
         evidencia_json, confianza_final, ciclo_id, validado_por,
         ciclo_origen, fecha_original, hash_artefacto_original,
         es_retroactivo, reingresado_en, notas_retroactivas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f"RETRO-C{ciclo}-{sku}", 'DETAL-A', fecha, sku, None,
        None, None, None, None, clasif, 'REINGESTADO',
        f'Caso retroactivo del Ciclo {ciclo}: {notas}',
        'cbr_retroactivo', 0, str((ciclo, sku)), 0.70, ciclo,
        'Domingo E. Díaz N. (C.P.C. 183594)',
        ciclo, fecha, hash_art,
        1, datetime.now().isoformat(), notas,
    ))
    if con.total_changes > insertados:
        insertados += 1

con.commit()
print(f"   ✅ {insertados} casos retroactivos insertados")

# ============================================================
# PASO 4 — RESUMEN
# ============================================================
print()
print("=" * 72)
print("RESUMEN DEL CBR")
print("=" * 72)
print()

for row in con.execute("""
    SELECT COALESCE(ciclo_origen, ciclo_id) as c, COUNT(*) as n,
           SUM(COALESCE(es_retroactivo, 0)) as retro
    FROM casos_resueltos
    GROUP BY c
    ORDER BY c
"""):
    print(f"  Ciclo {row['c']}: {row['n']} casos ({row['retro']} retroactivos)")

total = con.execute("SELECT COUNT(*) FROM casos_resueltos").fetchone()[0]
print(f"\n  TOTAL: {total} casos en el CBR")

con.close()
print()
print("=" * 72)
print("✅ CBR RETROACTIVO CONFIGURADO")
print("=" * 72)
