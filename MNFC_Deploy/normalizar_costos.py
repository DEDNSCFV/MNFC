import sqlite3
import os
import json
from decimal import Decimal, ROUND_HALF_EVEN
from mnfc.money import to_centimos, to_decimal

DB_ORIGEN = os.path.expanduser("~/DARTONY_EXTRACT/SCFV-DARTONY/inventario.db")
DB_DESTINO = "nodo_principal_dartony.db"

# Leer tasa BCV actual
with open("tasas_bcv.json", "r") as f:
    TASA_BCV = Decimal(json.load(f)["USD"])

print("="*70)
print(f"🔧 NORMALIZANDO COSTOS (Tasa BCV: {TASA_BCV})")
print("="*70)

con_o = sqlite3.connect(DB_ORIGEN)
con_d = sqlite3.connect(DB_DESTINO)
cur_o = con_o.cursor()
cur_d = con_d.cursor()

# Obtener los costos en VES de la tabla origen
cur_o.execute("""
    SELECT codigo, costo_unitario_ves, costo_unitario_usd
    FROM maestro_sku
    WHERE codigo IS NOT NULL AND codigo != ''
""")

actualizados = 0
for codigo, c_ves, c_usd in cur_o.fetchall():
    try:
        # Estrategia 1: usar costo VES / tasa BCV (fuente de verdad en VES)
        if c_ves and c_ves > 0:
            costo_usd_real = Decimal(str(c_ves)) / TASA_BCV
        # Estrategia 2: usar costo USD tal cual (si ya estaba bien)
        elif c_usd and c_usd > 0:
            costo_usd_real = Decimal(str(c_usd))
        else:
            continue
        
        costo_cent = to_centimos(costo_usd_real.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))
        
        cur_d.execute("""
            UPDATE inventario_nodo
            SET costo_unitario_cent = ?
            WHERE sku = ?
        """, (costo_cent, codigo.strip()))
        actualizados += 1
    except:
        pass

con_d.commit()
con_o.close()
con_d.close()

print(f"✅ {actualizados:,} costos normalizados")
print("="*70)
