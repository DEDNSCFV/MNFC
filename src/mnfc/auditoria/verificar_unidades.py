# verificar_unidades.py
import sqlite3, re

DB = r'C:\Users\Admin\Desktop\dartony_auditoria_v2.db'
TXT = r'C:\Users\Admin\Desktop\ARTÍCULOS CON SU PRECIO 13112026.TXT'

con = sqlite3.connect(DB)
cur = con.cursor()

# 1. Parsear TXT capturando SKU, descripción, precio Y unidad
patron = re.compile(r'\s+([\d,]+\.\d+)\s+(UNIDAD|\d{2}|KG|LT|MT|PAR|CAJA|DOCENA|CIENTO|JUEGO)\s*$')
precios_txt = {}
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
        unidad = m_precio.group(2)
        desc_start = m_sku.end()
        desc_end = linea.rfind(m_precio.group(0))
        descripcion = linea[desc_start:desc_end].strip() if desc_end > desc_start else ""
        if sku not in precios_txt:
            precios_txt[sku] = {
                'precio': precio,
                'unidad': unidad,
                'descripcion': descripcion[:80]
            }

print(f"SKUs en TXT: {len(precios_txt)}")

# 2. Cruzar con los 13 hallazgos
print("\n" + "="*110)
print("VERIFICACION DE UNIDADES - 13 HALLAZGOS")
print("="*110)
hallazgos = cur.execute("""
    SELECT sku, detal, hallazgo FROM decision
    WHERE aplicado_en_profit=0 AND decision_tomada='APLICAR'
    ORDER BY detal, sku
""").fetchall()

def get_dif(hall):
    m = re.search(r'(FALTANTE|SOBRANTE)\s+([+-]?\d+)', hall)
    return int(m.group(2)) if m else 0

print(f"{'SKU':<12} | {'SUCURSAL':<14} | {'DIF':>4} | {'PRECIO':>8} | {'UNIDAD':<8} | DESCRIPCION")
print("-"*110)

alertas = []
for sku, detal, hall in hallazgos:
    dif = get_dif(hall)
    info = precios_txt.get(sku)
    if not info:
        print(f"{sku:<12} | {detal:<14} | {dif:>+4} | {'N/A':>8} | {'N/A':<8} | NO ENCONTRADO EN TXT")
        continue
    precio = info['precio']
    unidad = info['unidad']
    desc = info['descripcion']
    desc_upper = desc.upper()

    flag = ""
    # Alerta 1: descripción sugiere caja/kit/par pero unidad dice UNIDAD
    palabras_compra = ['CAJA', 'KIT', 'PAR', 'DOCENA', 'CIENTO', 'JUEGO', 'PIEZAS']
    tiene_palabra_compra = any(p in desc_upper for p in palabras_compra)
    if tiene_palabra_compra and unidad == 'UNIDAD':
        flag = "*** AMBIGUEDAD (desc dice caja/kit/piezas pero unidad=UNIDAD)"
        alertas.append((sku, detal, desc, unidad, precio, dif, flag))
    # Alerta 2: unidad es explícitamente CAJA/PAR/etc
    elif unidad in ['CAJA', 'PAR', 'DOCENA', 'CIENTO', 'JUEGO']:
        flag = f"*** PRECIO POR {unidad}"
        alertas.append((sku, detal, desc, unidad, precio, dif, flag))
    # Alerta 3: descripción menciona "PIEZAS" pero unidad es UNIDAD (caso R-108)
    elif 'PIEZAS' in desc_upper:
        flag = "*** desc menciona PIEZAS - verificar si precio es por pieza o por caja"
        alertas.append((sku, detal, desc, unidad, precio, dif, flag))

    print(f"{sku:<12} | {detal:<14} | {dif:>+4} | ${precio:>7.2f} | {unidad:<8} | {desc[:50]}")
    if flag:
        print(f"  >>> {flag}")

# 3. Discrepancias BD vs TXT
print("\n" + "="*110)
print("DISCREPANCIAS ENTRE precio_sku (BD) Y TXT")
print("="*110)
for sku, detal, _ in hallazgos:
    r = cur.execute("SELECT unidad, precio FROM precio_sku WHERE sku=? OR sku_norm=?", (sku, sku)).fetchone()
    u_bd = r[0] if r and r[0] else 'N/A'
    p_bd = r[1] if r and r[1] else 0
    info = precios_txt.get(sku, {})
    u_txt = info.get('unidad', 'N/A')
    p_txt = info.get('precio', 0)
    if u_bd != u_txt or abs(p_bd - p_txt) > 0.001:
        print(f"  {sku:<12} | BD: ${p_bd:.2f} ({u_bd}) | TXT: ${p_txt:.2f} ({u_txt})")

# 4. Alertas críticas
print("\n" + "="*110)
print("ALERTAS CRITICAS")
print("="*110)
if alertas:
    print(f"  {len(alertas)} SKUs requieren verificacion manual:")
    print()
    for sku, detal, desc, unidad, precio, dif, flag in alertas:
        print(f"  [{sku}] {detal}")
        print(f"    Descripcion: {desc}")
        print(f"    Precio TXT: ${precio:.2f} | Unidad: {unidad} | Diferencia: {dif:+d}")
        print(f"    Impacto asumiendo precio POR UNIDAD: ${dif * precio:+.2f}")
        print(f"    {flag}")
        print()
else:
    print("  Sin alertas. Todos los precios son por UNIDAD o la unidad es explicita.")

# 5. Verificar si alguno de los 13 hallazgos es de producto con "CAJA" en descripción
print("="*110)
print("PRODUCTOS CON 'CAJA' O 'KIT' EN DESCRIPCION")
print("="*110)
for sku, detal, hall in hallazgos:
    info = precios_txt.get(sku, {})
    desc = info.get('descripcion', '').upper()
    if 'CAJA' in desc or 'KIT' in desc:
        print(f"  {sku:<12} | {detal:<14} | {info.get('descripcion', '')[:70]}")
        print(f"               Precio: ${info.get('precio', 0):.2f} | Unidad: {info.get('unidad', 'N/A')}")

con.close()