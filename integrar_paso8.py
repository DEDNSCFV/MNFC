#!/usr/bin/env python3
"""Integra pasos 7 y 8 al final de FLUJO_MAÑANA_v2.sh."""
from pathlib import Path

script = Path.home() / "FLUJO_MAÑANA_v2.sh"
texto = script.read_text(encoding='utf-8')

# Verificar si ya está integrado
if "[7/8]" in texto:
    print("⚠️ Ya integrado. No se duplica.")
    exit(0)

bloque_final = '''echo "════════════════════════════════════════════════════════════════"
echo "  ✅ MAÑANA COMPLETADA · $NODO_DB"
echo "  Procesados: $NUEVOS nuevos, $YA_PROCESADOS ya estaban"
echo "════════════════════════════════════════════════════════════════"'''

nuevo_bloque = '''# ============================================================
# PASO 7 — Calcular 24 KPIs del nodo
# ============================================================
echo "[7/8] Calculando 24 KPIs del nodo..."
mkdir -p "$BASE/control/kpis"
if [ -f "$HOME/MNFC/kpis_nodo_v3.py" ]; then
  python "$HOME/MNFC/kpis_nodo_v3.py" "$NODO_DB" "$NODO_TEC" 2>&1 | tail -30
else
  echo "  ⚠️ kpis_nodo_v3.py no encontrado"
fi
echo ""

# ============================================================
# PASO 8 — Calcular KPIs atómicos por SKU
# ============================================================
echo "[8/8] Calculando KPIs atómicos por SKU..."
if [ -f "$HOME/MNFC/kpis_reticulo_v4.py" ]; then
  python "$HOME/MNFC/kpis_reticulo_v4.py" "$NODO_DB" "$NODO_TEC" 2>&1 | tail -40
else
  echo "  ⚠️ kpis_reticulo_v4.py no encontrado"
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  ✅ MAÑANA COMPLETADA · $NODO_DB"
echo "  Procesados: $NUEVOS nuevos, $YA_PROCESADOS ya estaban"
echo "════════════════════════════════════════════════════════════════"'''

if bloque_final in texto:
    texto = texto.replace(bloque_final, nuevo_bloque)
    script.write_text(texto, encoding='utf-8')
    print("✅ Pasos 7 y 8 integrados.")
    print()
    print("Verificación:")
    contenido = script.read_text(encoding='utf-8')
    print(f"  ¿Tiene paso 7?: {'✅' if '[7/8]' in contenido else '❌'}")
    print(f"  ¿Tiene paso 8?: {'✅' if '[8/8]' in contenido else '❌'}")
    print(f"  Líneas totales: {len(contenido.split(chr(10)))}")
else:
    print("❌ No se encontró el bloque final exacto.")
    print("Revisar el archivo manualmente:")
    print(f"  tail -10 {script}")
