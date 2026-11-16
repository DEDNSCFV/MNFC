import sqlite3, re
DB = r'C:\Users\Admin\Desktop\dartony_auditoria_v2.db'
TXT = r'C:\Users\Admin\Desktop\ARTÍCULOS CON SU PRECIO 13112026.TXT'
con = sqlite3.connect(DB)
cur = con.cursor()

# 1. Parsear TXT
precios = {}
patron = re.compile(r'\s+([\d,]+\.\d+)\s+(UNIDAD|\d{2}|KG|LT|MT|PAR|CAJA)\s*$')
with open(TXT, encoding='latin-1', errors='replace') as fh:
    for linea in fh:
        if len(linea) < 50: continue
        m_sku = re.match(r'^(\S+)\s+', linea)
        if not m_sku: continue
        sku = m_sku.group(1).strip()
        if not sku or not sku[0].isalnum(): continue
        if any(h in linea for h in ['Código','Descripción','Profit','INVERSIONES','Página','Inventario']): continue
        m_precio = patron.search(linea)
        if not m_precio: continue
        try:
            precio = float(m_precio.group(1).replace(',', ''))
        except ValueError:
            continue
        if sku not in precios:
            precios[sku] = precio
print(f"SKUs parseados: {len(precios):,}")

# 2. UPSERT con sku_norm
ins = act = 0
for sku, precio in precios.items():
    sku_norm = sku.strip()
    r = cur.execute("SELECT precio FROM precio_sku WHERE sku=? OR sku_norm=?", (sku, sku_norm)).fetchone()
    if r is None:
        cur.execute("INSERT INTO precio_sku (sku, sku_norm, precio, fecha, archivo_origen) VALUES (?, ?, ?, ?, ?)",
                    (sku, sku_norm, precio, '13/11/2026', 'ARTÍCULOS CON SU PRECIO 13112026.TXT'))
        ins += 1
    elif abs((r[0] or 0) - precio) > 0.001:
        cur.execute("UPDATE precio_sku SET precio=?, fecha=?, archivo_origen=? WHERE sku=? OR sku_norm=?",
                    (precio, '13/11/2026', 'ARTÍCULOS CON SU PRECIO 13112026.TXT', sku, sku_norm))
        act += 1
con.commit()
print(f"Insertados: {ins} | Actualizados: {act}")

# 3. Precios de los 13 hallazgos
print("\n" + "="*90)
print("PRECIOS OFICIALES DE LOS 13 HALLAZGOS")
print("="*90)
hallazgos = cur.execute("SELECT sku, detal, hallazgo FROM decision WHERE aplicado_en_profit=0 AND decision_tomada='APLICAR' ORDER BY detal, sku").fetchall()
print(f"{'SKU':<12} | {'DETAL':<16} | {'PRECIO':>10} | HALLAZGO")
print("-"*90)
for sku, detal, hall in hallazgos:
    r = cur.execute("SELECT precio FROM precio_sku WHERE sku=? OR sku_norm=?", (sku, sku)).fetchone()
    p = f"${r[0]:.2f}" if r and r[0] else "SIN PRECIO"
    print(f"{sku:<12} | {detal:<16} | {p:>10} | {hall[:45]}")

# 4. Impacto monetario
print("\n" + "="*90)
print("IMPACTO MONETARIO (precios oficiales Profit)")
print("="*90)
def get_dif(hall):
    m = re.search(r'(FALTANTE|SOBRANTE)\s+([+-]?\d+)', hall)
    return int(m.group(2)) if m else 0
total = 0.0
por_suc = {}
print(f"{'SKU':<12} | {'DETAL':<16} | {'DIF':>5} | {'PRECIO':>9} | {'IMPACTO':>11} | MATERIAL")
print("-"*90)
for sku, detal, hall in hallazgos:
    dif = get_dif(hall)
    r = cur.execute("SELECT precio FROM precio_sku WHERE sku=? OR sku_norm=?", (sku, sku)).fetchone()
    if not r or not r[0]:
        print(f"{sku:<12} | {detal:<16} | {dif:>+5} | {'N/A':>9} | {'pendiente':>11} | -")
        continue
    impacto = dif * r[0]
    mat = "SI" if abs(impacto) >= 10 else "no"
    print(f"{sku:<12} | {detal:<16} | {dif:>+5} | ${r[0]:>8.2f} | ${impacto:>+10.2f} | {mat}")
    total += impacto
    por_suc[detal] = por_suc.get(detal, 0) + impacto
print("-"*90)
print(f"{'TOTAL':<12} | {'':<16} | {'':>5} | {'':>9} | ${total:>+10.2f} |")
print("\nPor sucursal:")
for s in sorted(por_suc.keys()):
    mat = "MATERIAL" if abs(por_suc[s]) >= 10 else "inmaterial"
    print(f"  {s:<20}: ${por_suc[s]:>+10.2f}  ({mat})")
con.close()