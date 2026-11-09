import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

DB = Path.home() / "dartony_auditoria.db"
FECHA_HOY = datetime.now().strftime("%Y-%m-%d")
ARCHIVO_SALIDA = Path.home() / f"INFORME_DIARIO_DARTONY_{FECHA_HOY}.md"

con = sqlite3.connect(DB)
cur = con.cursor()

# --- 1. DATOS DEL RESUMEN ---
cur.execute("""
    SELECT COUNT(*), 
           SUM(CASE WHEN c.cantidad_fisica != (SELECT stock_cent/100.0 FROM v_movimientos_centimos v WHERE v.sku = c.sku ORDER BY v.id DESC LIMIT 1) THEN 1 ELSE 0 END)
    FROM conteo_fisico c
    WHERE c.cantidad_fisica > 0
""")
resumen = cur.fetchone()
total_skus_contados = resumen[0] if resumen[0] else 0
skus_con_diferencia = resumen[1] if resumen[1] else 0

# --- 2. TOP 5 FALTANTES (Corregido: c.empresa en vez de c.detal) ---
cur.execute("""
    SELECT c.empresa, c.sku, c.descripcion, c.cantidad_fisica,
           (SELECT stock_cent/100.0 FROM v_movimientos_centimos v WHERE v.sku = c.sku ORDER BY v.id DESC LIMIT 1) AS stock_profit,
           (c.cantidad_fisica - (SELECT stock_cent/100.0 FROM v_movimientos_centimos v WHERE v.sku = c.sku ORDER BY v.id DESC LIMIT 1)) AS diferencia
    FROM conteo_fisico c
    WHERE c.cantidad_fisica > 0 AND diferencia != 0
    ORDER BY diferencia ASC
    LIMIT 5
""")
top_faltantes = cur.fetchall()

# --- 3. ESTADO DEL CICLO ---
cur.execute("SELECT estado, observacion FROM ciclo_diario WHERE fecha = ? LIMIT 1", (FECHA_HOY,))
estado_ciclo = cur.fetchone()
estado = estado_ciclo[0] if estado_ciclo else "NO_REGISTRADO"
obs = estado_ciclo[1] if estado_ciclo and estado_ciclo[1] else "Sin observaciones"

# --- 4. HALLAZGOS EXTRA ---
cur.execute("SELECT COUNT(*), SUM(impacto_estimado_centimos)/100.0 FROM hallazgo_extra WHERE fecha = ?", (FECHA_HOY,))
extras = cur.fetchone()
total_extras = extras[0] if extras[0] else 0
impacto_extras = extras[1] if extras[1] else 0.0

# --- 5. GENERAR EL TEXTO DEL DOCUMENTO ---
texto_informe = f"""# INFORME DIARIO DE AUDITORÍA - DARTONY
**Fecha:** {FECHA_HOY}
**Auditor:** Domingo E. Díaz N. (C.P.C. 183594)
---

## 1. Resumen Ejecutivo
- **Estado del Ciclo:** {estado}
- **Observación:** {obs}
- **SKUs Auditados:** {total_skus_contados}
- **SKUs con Diferencia:** {skus_con_diferencia}
- **Hallazgos Imprevistos:** {total_extras} (Impacto: ${impacto_extras:.2f})

## 2. Top 5 Faltantes Críticos (Alerta Operativa)
| Empresa/Detal | SKU | Descripción | Conteo Físico | Stock Profit | Diferencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""

for row in top_faltantes:
    texto_informe += f"| {row[0]} | {row[1]} | {row[2][:30]}... | {row[3]} | {row[4]} | **{row[5]}** |\n"

texto_informe += f"""
## 3. Nota de Auditoría (NIA 501)
El presente informe ha sido generado automáticamente por el Sistema Experto SCFV. 
Las diferencias aquí expuestas requieren la verificación física in situ y la firma de resolución en la tabla `decision` antes de su aplicación en Profit.

*Este documento es un borrador técnico. Requiere la revisión y firma del C.P.C. para su validez legal.*
"""

# --- 6. GUARDAR EL ARCHIVO ---
with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
    f.write(texto_informe)

# --- 7. GENERAR HASH SHA256 Y REGISTRAR EN LA BD ---
hash_informe = hashlib.sha256(texto_informe.encode('utf-8')).hexdigest()

try:
    cur.execute("""
        INSERT INTO firma_auditor (cpc, nombre, datos_firmados, timestamp, hash_anterior, hash_firma)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ('183594', 'Domingo E. Díaz N.', f'Informe Diario {FECHA_HOY}', FECHA_HOY, 'GENESIS', hash_informe))
    con.commit()
    print(f"✅ Informe generado en: {ARCHIVO_SALIDA}")
    print(f"🔒 Hash SHA256 del informe: {hash_informe}")
except Exception as e:
    print(f"Error al guardar la firma: {e}")

con.close()
