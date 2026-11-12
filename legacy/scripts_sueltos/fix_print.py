#!/usr/bin/env python3
"""Arregla el print que falla con None."""
from pathlib import Path

src = Path.home() / "MNFC" / "kpis_reticulo_v3.py"
texto = src.read_text(encoding='utf-8')

# Reemplazar el print problemático
texto = texto.replace(
    '''kpis_por_sku.sort(key=lambda x: -x['valor'])
for k in kpis_por_sku[:10]:
    print(f"  {k['sku']:15s}: stock={k['stock']:>8.0f} | ${k['valor']:>12,.0f} | rot={k['rotacion']:>6.2f}x | días={k['dias_inventario']:>6.1f} | ruptura={k['tiempo_ruptura']:>6.1f}d")
print()''',
    '''kpis_por_sku.sort(key=lambda x: -x['valor'])
print(f"  {'SKU':15s} {'Stock':>8s} {'Valor':>12s} {'Rotación':>10s} {'Días':>8s} {'Ruptura':>8s} {'Estado':>20s}")
print("  " + "-" * 90)
for k in kpis_por_sku[:15]:
    rot_str = f"{k['rotacion']:.2f}x" if k['rotacion'] is not None else "—"
    dias_str = f"{k['dias_inventario']:.1f}" if k['dias_inventario'] is not None else "—"
    rupt_str = f"{k['tiempo_ruptura']:.1f}d" if k['tiempo_ruptura'] is not None else "—"
    print(f"  {k['sku']:15s} {k['stock']:>8.0f} ${k['valor']:>11,.0f} {rot_str:>10s} {dias_str:>8s} {rupt_str:>8s} {k.get('estado', ''):>20s}")
print()''')

# También arreglar el estadísticas para filtrar None
texto = texto.replace(
    '''rotaciones = [k['rotacion'] for k in kpis_por_sku if k['rotacion'] > 0]''',
    '''rotaciones = [k['rotacion'] for k in kpis_por_sku if k['rotacion'] is not None and k['rotacion'] > 0]'''
)

dst = Path.home() / "MNFC" / "kpis_reticulo_v4.py"
dst.write_text(texto, encoding='utf-8')
print(f"Script corregido: {dst}")
