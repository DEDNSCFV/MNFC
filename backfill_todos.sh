#!/data/data/com.termux/files/usr/bin/bash
# Backfill completo para los 3 nodos restantes
# Usa backfill_v2 (el corregido para fechas)

NODOS=("01 Central" "05 Cúa" "06 TERE")

for nodo in "${NODOS[@]}"; do
  echo ""
  echo "════════════════════════════════════════════════════════════════"
  echo "  BACKFILL: $nodo"
  echo "════════════════════════════════════════════════════════════════"
  echo ""

  echo "[1/3] Mensual..."
  python ~/MNFC/backfill_v2.py "$nodo" mensual 2>&1 | grep -E "✅"
  echo ""

  echo "[2/3] Semanal..."
  python ~/MNFC/backfill_v2.py "$nodo" semanal 2>&1 | grep -E "✅"
  echo ""

  echo "[3/3] Diario..."
  python ~/MNFC/backfill_v2.py "$nodo" diario 2>&1 | grep -E "✅"
  echo ""

  echo "  ✅ $nodo completado"
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  TODOS LOS NODOS COMPLETADOS"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Verificación:"
for nodo in "01_Central" "04_La_Urbina" "05_Cua" "06_TERE"; do
  DIR="$HOME/DARTONY_CONTROL/$nodo/historico"
  if [ -d "$DIR" ]; then
    M=$(find "$DIR/mensual" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    S=$(find "$DIR/semanal" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    D=$(find "$DIR/diario" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    T=$(du -sh "$DIR" 2>/dev/null | cut -f1)
    echo "  $nodo:"
    echo "    Mensual: $M | Semanal: $S | Diario: $D"
    echo "    Tamaño:  $T"
  fi
done
