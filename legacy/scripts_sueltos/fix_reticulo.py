#!/usr/bin/env python3
"""Acota el tiempo hasta ruptura y separa SKUs con demanda insuficiente."""
from pathlib import Path

src = Path.home() / "MNFC" / "kpis_reticulo_v2.py"
texto = src.read_text(encoding='utf-8')

# Reemplazar el bloque de KPIs por SKU para acotar
texto = texto.replace(
    '''kpis_por_sku = []
for sku in A:
    attrs = skus[sku]
    if attrs['stock'] > 0 and attrs['demanda_diaria'] > 0:
        rot = (attrs['demanda_diaria'] * 365) / attrs['stock'] if attrs['stock'] else 0
        dias = 365 / rot if rot else 0
        ruptura = attrs['stock'] / attrs['demanda_diaria'] if attrs['demanda_diaria'] else 0
        kpis_por_sku.append({
            'sku': sku,
            'stock': attrs['stock'],
            'valor': attrs['valor'],
            'demanda_diaria': attrs['demanda_diaria'],
            'rotacion': round(rot, 2),
            'dias_inventario': round(dias, 1),
            'tiempo_ruptura': round(ruptura, 1),
        })''',
    '''kpis_por_sku = []
for sku in A:
    attrs = skus[sku]
    if attrs['stock'] <= 0:
        continue
    if attrs['demanda_diaria'] < 0.1:
        # Demanda insuficiente: no se calcula rotación ni ruptura
        kpis_por_sku.append({
            'sku': sku,
            'stock': attrs['stock'],
            'valor': attrs['valor'],
            'demanda_diaria': round(attrs['demanda_diaria'], 4),
            'rotacion': None,
            'dias_inventario': None,
            'tiempo_ruptura': None,
            'estado': 'DEMANDA_INSUFICIENTE',
        })
        continue
    rot = (attrs['demanda_diaria'] * 365) / attrs['stock']
    dias = 365 / rot if rot else 0
    ruptura = attrs['stock'] / attrs['demanda_diaria']
    # Acotar a 365 días máximo
    ruptura_acotada = min(ruptura, 365)
    kpis_por_sku.append({
        'sku': sku,
        'stock': attrs['stock'],
        'valor': attrs['valor'],
        'demanda_diaria': round(attrs['demanda_diaria'], 2),
        'rotacion': round(rot, 2),
        'dias_inventario': round(dias, 1),
        'tiempo_ruptura': round(ruptura_acotada, 1),
        'ruptura_real': round(ruptura, 1),
        'estado': 'CALCULADO',
    })'''
)

dst = Path.home() / "MNFC" / "kpis_reticulo_v3.py"
dst.write_text(texto, encoding='utf-8')
print(f"Script corregido: {dst}")
