import sqlite3
from mnfc.money import to_decimal

con = sqlite3.connect("mnfc_produccion.db")
cur = con.cursor()

print("="*70)
print("CONSULTA A LA BASE DE DATOS: INVENTARIO OPERATIVO")
print("="*70)
cur.execute("SELECT sku, nombre, cantidad_fisica, costo_unitario_cent, fecha_hora_registro FROM inventario")
for row in cur.fetchall():
    sku, nombre, cant, costo_cent, fecha = row
    print(f"{sku:8} | {nombre:22} | Cant: {cant:4} | Costo: ${to_decimal(costo_cent):>6} | Hora: {fecha}")
print("="*70)
con.close()
