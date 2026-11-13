import sqlite3
import json
from decimal import Decimal

DB = "nodo_principal_dartony.db"

with open("tasas_bcv.json", "r") as f:
    TASA_BCV = Decimal(json.load(f)["USD"])

print("="*70)
print(f"🔧 NORMALIZANDO COSTOS DE 462K MOVIMIENTOS (Tasa BCV: {TASA_BCV})")
print("="*70)

con = sqlite3.connect(DB)
cur = con.cursor()

cur.execute("SELECT COUNT(*) FROM movimientos_dartony WHERE costo_unitario_cent > 0")
total_con_costo = cur.fetchone()[0]
print(f"📊 Movimientos con costo registrado: {total_con_costo:,}")

# El costo_unitario_cent guardado era en VES/centavos, lo pasamos a USD/centavos
cur.execute("""
    UPDATE movimientos_dartony
    SET costo_unitario_cent = CAST(costo_unitario_cent / ? AS INTEGER)
    WHERE costo_unitario_cent > 0
""", (float(TASA_BCV),))

con.commit()
print(f"✅ {cur.rowcount:,} movimientos normalizados a USD")

cur.execute("""
    SELECT SUM(ABS(cantidad) * costo_unitario_cent)
    FROM movimientos_dartony
    WHERE tipo LIKE '%FACT%' OR tipo LIKE '%VENTA%'
""")
nuevo_costo_ventas = cur.fetchone()[0] or 0

cur.execute("SELECT SUM(cantidad_fisica * costo_unitario_cent) FROM inventario_nodo")
costo_inventario = cur.fetchone()[0] or 0

print(f"\n📈 Verificación:")
print(f"   Costo Ventas Normalizado : ${Decimal(nuevo_costo_ventas) / 100:,.2f} USD")
print(f"   Costo Inventario Actual  : ${Decimal(costo_inventario) / 100:,.2f} USD")
if costo_inventario > 0:
    rotacion = Decimal(nuevo_costo_ventas) / Decimal(costo_inventario)
    print(f"   Rotación Global          : {rotacion:.2f} veces")

con.close()
print("="*70)
