import sqlite3
import os
from decimal import Decimal
from mnfc.money import to_decimal

DB_ORIGEN = os.path.expanduser("~/DARTONY_EXTRACT/SCFV-DARTONY/inventario.db")

print("="*70)
print("🔍 AUDITORÍA DE COSTOS: DARTONY vs MNFC")
print("="*70)

con = sqlite3.connect(DB_ORIGEN)
cur = con.cursor()

# Ver los primeros 3 productos y sus 3 columnas de precio
cur.execute("""
    SELECT codigo, descripcion, precio_unitario_usd, costo_unitario_ves, costo_unitario_usd 
    FROM maestro_sku 
    WHERE codigo IN ('6238', 'ROS37536', 'MO-104')
""")

print(f"{'SKU':<12} | {'PRECIO_USD':<12} | {'COSTO_VES':<15} | {'COSTO_USD':<12}")
print("-" * 70)
for row in cur.fetchall():
    codigo, desc, p_usd, c_ves, c_usd = row
    print(f"{codigo:<12} | ${p_usd:<11} | Bs. {c_ves:<11} | ${c_usd:<11}")

con.close()
print("-" * 70)
print("Si COSTO_USD es mayor que PRECIO_USD, la columna está en VES.")
