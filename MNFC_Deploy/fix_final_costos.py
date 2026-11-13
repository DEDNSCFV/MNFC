import sqlite3
from decimal import Decimal
from mnfc.money import to_centimos

DB = "nodo_principal_dartony.db"
con = sqlite3.connect(DB)
cur = con.cursor()

print("="*70)
print("🔧 NORMALIZACIÓN INTELIGENTE DE COSTOS (Dartony)")
print("="*70)

# Traer todos los SKUs con su stock, costo y precio actual
cur.execute("""
    SELECT sku, cantidad_fisica, costo_unitario_cent, precio_venta_cent
    FROM inventario_nodo
""")
productos = cur.fetchall()

corregidos_total = 0
corregidos_estimados = 0
eliminados = 0
ok = 0

for sku, cant, costo_cent, precio_cent in productos:
    # Caso 1: costo=0 y precio=0 → sin valoración, eliminar
    if costo_cent == 0 and precio_cent == 0:
        cur.execute("DELETE FROM inventario_nodo WHERE sku = ?", (sku,))
        eliminados += 1
        continue
    
    # Caso 2: costo=0 pero hay precio → estimar 60% del precio
    if costo_cent == 0 and precio_cent > 0:
        costo_nuevo = int(Decimal(precio_cent) * Decimal("0.60"))
        cur.execute("UPDATE inventario_nodo SET costo_unitario_cent = ? WHERE sku = ?", (costo_nuevo, sku))
        corregidos_estimados += 1
        continue
    
    # Caso 3: el costo es mayor al doble del precio → el "costo" era el total de la compra
    if cant > 0 and costo_cent > precio_cent * 2:
        # Hipótesis: el costo real es "costo / cantidad"
        costo_unitario_hipotesis = costo_cent // cant
        
        if costo_unitario_hipotesis <= precio_cent * Decimal("1.5"):
            # Tiene sentido: el "costo" era el total, no el unitario
            cur.execute("UPDATE inventario_nodo SET costo_unitario_cent = ? WHERE sku = ?", (costo_unitario_hipotesis, sku))
            corregidos_total += 1
        else:
            # No tiene sentido → estimar 60% del precio
            costo_nuevo = int(Decimal(precio_cent) * Decimal("0.60"))
            cur.execute("UPDATE inventario_nodo SET costo_unitario_cent = ? WHERE sku = ?", (costo_nuevo, sku))
            corregidos_estimados += 1
        continue
    
    ok += 1

con.commit()

# Verificación final
cur.execute("SELECT COUNT(*), SUM(cantidad_fisica * costo_unitario_cent), SUM(cantidad_fisica * precio_venta_cent) FROM inventario_nodo")
total, costo_cent, venta_cent = cur.fetchone()

print(f"\n📊 RESULTADOS DE LA CORRECCIÓN:")
print(f"  ✅ SKUs con datos coherentes          : {ok:,}")
print(f"  🔧 SKUs con costo unitario corregido  : {corregidos_total:,}")
print(f"  🔧 SKUs con costo estimado (60%)      : {corregidos_estimados:,}")
print(f"  🗑️  SKUs eliminados (sin valoración)   : {eliminados:,}")
print(f"\n  📦 Total SKUs finales                 : {total:,}")
print(f"  💰 Costo Total                        : ${Decimal(costo_cent) / 100:,.2f} USD")
print(f"  💵 Venta Total                        : ${Decimal(venta_cent) / 100:,.2f} USD")

margen = Decimal(venta_cent - costo_cent) / 100
print(f"  📈 Margen Bruto Potencial             : ${margen:,.2f} USD")

con.close()
print("="*70)
