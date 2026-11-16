# arqueologia_r108_char.py
import os

# Buscar archivo
archivo = None
for f in os.listdir(r'C:\Users\Admin\Desktop'):
    if 'MOVIMIENTOS' in f.upper() and 'CHARALLAVE' in f.upper() and 'AM2' in f.upper():
        archivo = os.path.join(r'C:\Users\Admin\Desktop', f)
        break

if not archivo:
    print("NO ENCONTRADO: MOVIMIENTOS CHARALLAVE AM2")
    exit(1)

print(f"Archivo: {os.path.basename(archivo)}")
print(f"Tamano: {os.path.getsize(archivo)/1024:.1f} KB")
print("="*100)

# Leer y buscar sección R-108
lineas = []
with open(archivo, encoding='latin-1', errors='replace') as fh:
    for linea in fh:
        lineas.append(linea.rstrip('\r\n'))

print(f"Total lineas: {len(lineas):,}")

# Encontrar dónde empieza R-108 (línea de artículo)
idx_inicio = None
idx_siguiente = None
for i, l in enumerate(lineas):
    # Línea de artículo: SKU al inicio + descripción
    if l.startswith('R-108') and len(l) > 30:
        if idx_inicio is None:
            idx_inicio = i
        else:
            # Encontró el siguiente SKU, marcar fin
            idx_siguiente = i
            break

if idx_inicio is None:
    print("\nR-108 NO ENCONTRADO en el archivo")
    # Mostrar los primeros SKUs para ver el formato
    print("\nPrimeras 30 lineas con SKU (chars 0-80):")
    count = 0
    for i, l in enumerate(lineas):
        if len(l) > 30 and l[0].isalnum() and not l.startswith(' '):
            print(f"  [{i:>5}] {repr(l[:80])}")
            count += 1
            if count >= 30:
                break
    exit(1)

print(f"\n{'='*100}")
print(f"SECCION R-108 ENCONTRADA: lineas {idx_inicio+1} a {idx_siguiente if idx_siguiente else len(lineas)}")
print("="*100)

# Extraer bloque (hasta el siguiente SKU o fin de archivo)
fin = idx_siguiente if idx_siguiente else min(idx_inicio + 200, len(lineas))
bloque = lineas[idx_inicio:fin]

print(f"\nTotal lineas en bloque: {len(bloque)}")
print()
for j, l in enumerate(bloque):
    # Truncar líneas muy largas
    if len(l) > 180:
        l_show = l[:180] + "..."
    else:
        l_show = l
    print(f"[{j:>3}] {repr(l_show)}")

# Análisis: extraer movimientos
print(f"\n{'='*100}")
print("ANALISIS DE MOVIMIENTOS")
print("="*100)

import re
movimientos = []
for j, l in enumerate(bloque[1:], 1):  # Saltar línea del artículo
    # Buscar patrones de movimiento: tipo + fecha + cantidad
    # Ejemplo típico Profit: "  FACT  15/10/2026  12345  ...  -1.00"
    m = re.match(r'\s+(FACT|NENT|NREC|AJUE|AJUS|DCLI|DPRO)\s+', l)
    if m:
        tipo = m.group(1)
        # Buscar fecha DD/MM/YYYY
        m_fecha = re.search(r'(\d{2}/\d{2}/\d{4})', l)
        fecha = m_fecha.group(1) if m_fecha else '?'
        # Buscar cantidad (último número con decimales o signo)
        # Buscar todos los números al final
        m_cant = re.findall(r'(-?\d+\.\d+)\s*$', l)
        cant = m_cant[-1] if m_cant else '?'
        movimientos.append({'linea': j, 'tipo': tipo, 'fecha': fecha, 'cant': cant, 'raw': l})

print(f"Movimientos detectados: {len(movimientos)}")
print(f"\n{'#':>3} | {'TIPO':<6} | {'FECHA':<12} | {'CANT':>8}")
print("-"*40)
suma = 0.0
for k, m in enumerate(movimientos, 1):
    print(f"{k:>3} | {m['tipo']:<6} | {m['fecha']:<12} | {m['cant']:>8}")
    try:
        suma += float(m['cant'])
    except:
        pass

print("-"*40)
print(f"SUMA DE MOVIMIENTOS: {suma:+.2f}")

# Buscar stock final en el bloque
print(f"\n{'='*100}")
print("BUSQUEDA DE STOCK FINAL / DIFERENCIA")
print("="*100)
for l in bloque:
    if any(k in l.upper() for k in ['SUB-TOTAL', 'SUBTOTAL', 'DIFERENCIA', 'TOTAL']):
        print(f"  {repr(l[:180])}")