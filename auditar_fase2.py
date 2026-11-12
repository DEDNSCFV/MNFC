#!/usr/bin/env python3
"""Inventario de fase 2 (callers con float). No bloquea fase 1."""
import sys, re, subprocess
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent


def main():
    print("=" * 60); print("INVENTARIO — FASE 2 (migración de callers)"); print("=" * 60)

    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        capture_output=True, text=True, cwd=ROOT,
    )
    fallos = re.findall(r"FAILED (\S+)", r.stdout)
    archivos = Counter(f.split("::")[0] for f in fallos)

    print(f"\nTotal fallos fase 2: {len(fallos)}")
    print("Archivos afectados:")
    for f, n in archivos.most_common():
        print(f"  {n:3d}  {f}")

    print("\nDetalle:")
    for f in fallos:
        print(f"  ❌ {f}")

    print(f"\n{'✅ Cero fallos fase 2' if not fallos else f'⏳ {len(fallos)} pendientes de migración'}")
    return 0 if not fallos else 1


if __name__ == "__main__":
    sys.exit(main())
