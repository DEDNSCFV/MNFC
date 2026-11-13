import sqlite3
from decimal import Decimal, ROUND_HALF_EVEN
from mnfc.money import to_centimos, to_decimal

DB_DESTINO = "nodo_principal_dartony.db"

con = sqlite3.connect(DB_DESTINO)
cur = con.cursor()

# Ver cuántos productos tienen costo = 0 pero precio > 0
cur.execute("""
    SELECT COUNT(*) FROM inventario_nodo 
    WHERE costo_unitario_cent = 0 AND precio_venta_cent > 0
""")
faltantes = cur.fetchone()[0]
print(f"📦 Productos con costo=0 pero precio>0: {faltantes:,}")

if faltantes > 0:
    # Estimar costo como 60% del precio de venta (margen 40%)
    MARGEN_COSTO = Decimal("0.60")
    
    cur.execute("""
        SELECT sku, precio_venta_cent FROM inventario_nodo 
        WHERE costo_unitario_cent = 0 AND precio_venta_cent > 0
    """)
    actualizados = 0
    for sku, precio_cent in cur.fetchall():
        costo_estimado = int(Decimal(precio_cent) * MARGEN_COSTO)
        cur.execute(
            "UPDATE inventario_nodo SET costo_unitario_cent = ? WHERE sku = ?",
            (costo_estimado, sku)
        )
        actualizados += 1
    
    con.commit()
    print(f"✅ {actualizados:,} costos estimados (60% del precio de venta)")

# Verificar el estado final
cur.execute("""
    SELECT COUNT(*) FROM inventario_nodo 
    WHERE costo_unitario_cent = 0
""")
sin_costo = cur.fetchone()[0]
print(f"📊 Productos sin costo (aún): {sin_costo:,}")

con.close()
