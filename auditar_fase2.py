#!/usr/bin/env python3
"""Inventario de fase 2 — progreso de migración, no regresiones.

Fase 2 migra el kernel de float a centavos (ADR-003, ADR-004).
Mide:
  - Sub-fases cerradas (por commit y por estado del código)
  - Tests rotos (regresión)
  - Estado general: EN_PROGRESO | COMPLETA
"""
import sys
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent

SUB_FASES = [
    ("2.1", "Propiedades monto_cent derivadas en ambas capas",
     lambda: _tiene(ROOT / "src/mnfc/mnfc.py", "total_debe_cent")
             and _tiene(ROOT / "src/mnfc/extensiones/modelos.py", "def monto_cent")),
    ("2.2", "mnfc.Asiento usa centavos como fuente de verdad",
     lambda: _tiene(ROOT / "src/mnfc/mnfc.py", "total_debe_cent: int")),
    ("2.3", "PartidaAutorizada.monto_cent como fuente de verdad",
     lambda: _tiene(ROOT / "src/mnfc/extensiones/modelos.py", "monto_cent: int")),
    ("2.4", "LineaAsiento/Asiento centavos como fuente",
     lambda: _tiene(ROOT / "src/mnfc/extensiones/modelos.py", "total_debe_cent: int")),
    ("2.5", "assembler._validar_monto acepta int centavos",
     lambda: _acepta_int(ROOT / "src/mnfc/dsl/assembler.py")),
    ("2.6", "Float eliminado + tag v0.5.0",
     lambda: _sin_float(ROOT / "src/mnfc/mnfc.py")
             and _sin_float(ROOT / "src/mnfc/extensiones/modelos.py")),
]


def _tiene(path: Path, needle: str) -> bool:
    return path.exists() and needle in path.read_text()


def _acepta_int(path: Path) -> bool:
    if not path.exists():
        return False
    txt = path.read_text()
    # 2.5: la validación ya no convierte a float sino a centavos
    return "to_centimos" in txt and "return float(monto)" not in txt


def _sin_float(path: Path) -> bool:
    if not path.exists():
        return False
    txt = path.read_text()
    return ": float" not in txt and "total_debe: float" not in txt


def main():
    print("=" * 60)
    print("INVENTARIO — FASE 2 (progreso de migración)")
    print("=" * 60)

    # Sub-fases
    cerradas = []
    pendientes = []
    print("\nSub-fases:")
    for num, desc, check in SUB_FASES:
        try:
            ok = check()
        except Exception as e:
            ok = False
        marca = "✅" if ok else "⏳"
        print(f"  {marca} {num}  {desc}")
        (cerradas if ok else pendientes).append(num)

    # Suite
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        capture_output=True, text=True, cwd=ROOT,
    )
    fallos = re.findall(r"FAILED (\S+)", r.stdout)
    pasa = r.returncode == 0

    print(f"\nSuite: {'✅ verde' if pasa else f'❌ {len(fallos)} fallos'}")
    if fallos:
        for f in fallos[:10]:
            print(f"  ❌ {f}")

    # Estado
    total = len(SUB_FASES)
    n_cerradas = len(cerradas)

    print(f"\nProgreso: {n_cerradas}/{total} sub-fases cerradas")
    if pendientes:
        print(f"Pendientes: {', '.join(pendientes)}")

    if n_cerradas == total and pasa:
        print("\n🎉 FASE 2 COMPLETA — kernel en centavos")
        return 0
    elif n_cerradas == 0 and not pasa:
        print("\n🔴 Fase 2 no iniciada y suite rota")
        return 2
    else:
        print(f"\n🟡 Fase 2 EN PROGRESO — faltan {total - n_cerradas} sub-fases")
        return 1


if __name__ == "__main__":
    sys.exit(main())
