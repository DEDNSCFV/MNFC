import sqlite3
from mnfc.money import to_decimal

con = sqlite3.connect("nodo_principal_dartony.db")
cur = con.cursor()

print("=== INVENTARIO (Tabla de Dominio) ===")
cur.execute("SELECT sku, nombre, cantidad_fisica, costo_unitario_cent FROM inventario_nodo")
for row in cur.fetchall():
    print(f"{row[0]:8} | {row[1]:22} | Cant: {row[2]:4} | Costo: ${to_decimal(row[3])}")

print("\n=== LEDGER (Eventos Inmutables) ===")
cur.execute("SELECT tipo_evento, timestamp_seniat, hash_evento FROM eventos_ledger")
for row in cur.fetchall():
    print(f"{row[0]:22} | {row[1]} | Hash: {row[2]}")

con.close()
