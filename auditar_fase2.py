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
             and _tiene(ROOT / "src/mnfc/extensiones/modelos.py", "monto_cent")),
    ("2.2", "mnfc.Asiento usa centavos como fuente de verdad",
     lambda: _tiene(ROOT / "src/mnfc/mnfc.py", "total_debe_cent: int")),
    ("2.3", "PartidaAutorizada.monto_cent como fuente de verdad",
     lambda: _partida_autorizada_migrada(ROOT / "src/mnfc/extensiones/modelos.py")),
    ("2.4a", "Asiento centavos como fuente",
     lambda: _tiene(ROOT / "src/mnfc/extensiones/modelos.py", "_total_debe_cent")),
    ("2.4b", "LineaAsiento centavos como fuente",
     lambda: _tiene(ROOT / "src/mnfc/extensiones/modelos.py", "monto_cent: int")),
    ("2.5", "assembler._validar_monto acepta int centavos",
     lambda: _acepta_int(ROOT / "src/mnfc/dsl/assembler.py")),
    ("2.6", "Float eliminado + compat @property removida + tag v0.5.0",
     lambda: _sin_property_float(ROOT / "src/mnfc/mnfc.py")
             and _sin_property_float(ROOT / "src/mnfc/extensiones/modelos.py")
             and _sin_raw(ROOT / "src/mnfc/extensiones/modelos.py")
             and _tag_v050_existe()),
]


def _partida_autorizada_migrada(path: Path) -> bool:
    """2.3: PartidaAutorizada tiene monto_cent como field (dentro del bloque de la clase)."""
    if not path.exists():
        return False
    txt = path.read_text()
    # Extraer bloque PartidaAutorizada
    import re as _re
    m = _re.search(r'class PartidaAutorizada:.*?(?=\n\n@dataclass|\n\nclass |\Z)', txt, _re.DOTALL)
    if not m:
        return False
    bloque = m.group(0)
    return "monto_cent: int" in bloque


def _tiene(path: Path, needle: str) -> bool:
    return path.exists() and needle in path.read_text()


def _acepta_int(path: Path) -> bool:
    if not path.exists():
        return False
    txt = path.read_text()
    # 2.5: la validación ya no convierte a float sino a centavos
    return "to_centimos" in txt and "return float(monto)" not in txt


def _sin_property_float(path: Path) -> bool:
    """Sin @property monto/total_* -> float en el archivo."""
    if not path.exists():
        return False
    txt = path.read_text()
    import re as _re
    # Buscar @property seguido de def monto/total_*
    patron = _re.compile(
        r'@property\s*\n\s*def (monto|total_debe|total_haber)\s*\(.*?\)\s*->\s*float',
        _re.DOTALL,
    )
    return not patron.search(txt)


def _sin_raw(path: Path) -> bool:
    """Sin atributos _monto_raw / _total_*_raw."""
    if not path.exists():
        return False
    txt = path.read_text()
    return "_monto_raw" not in txt and "_total_debe_raw" not in txt


def _tag_v050_existe() -> bool:
    import subprocess as _sp
    try:
        r = _sp.run(
            ["git", "tag", "-l", "v0.5.0*"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        return bool(r.stdout.strip())
    except Exception:
        return False


def _sin_float_campos(path: Path) -> bool:
    """Sin anotaciones de campo float para monto/total_*."""
    if not path.exists():
        return False
    txt = path.read_text()
    import re as _re
    # Buscar líneas que empiezan con 4 espacios y son anotaciones de campo
    for _ in _re.finditer(
        r'^\s{4}(monto|total_debe|total_haber)\s*:\s*float',
        txt, _re.MULTILINE
    ):
        return False
    return True


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
