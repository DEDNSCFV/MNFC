#!/usr/bin/env python3
"""Certifica SOLO fase 1 (frontera monetaria). Sale 0 si fase 1 OK."""
import sys, re, subprocess
from pathlib import Path

ROOT = Path(__file__).parent
errores = []


def check_schema():
    p = ROOT / "schema_limpio.sql"
    if not p.exists():
        errores.append("schema_limpio.sql ausente"); return
    for i, linea in enumerate(p.read_text().splitlines(), 1):
        limpia = linea.split("--")[0]
        if re.search(r"\bREAL\b", limpia, re.I):
            if not any(c in limpia for c in ("cantidad_fisica", "peso")):
                errores.append(f"schema_limpio.sql:{i}: REAL en columna monetaria → {linea.strip()}")


def check_codigo():
    # Fase 1 = frontera monetaria. El kernel (assembler.py) queda en float
    # por decisión arquitectónica; su migración es fase 2.
    checks = {
        "src/mnfc/baldor_centimos.py": "monto: float",  # nunca debe volver
    }
    for f, patron in checks.items():
        p = ROOT / f
        if p.exists() and patron in p.read_text():
            errores.append(f"{f}: todavía acepta float ({patron!r})")


def check_imports():
    if not (ROOT / "src/mnfc/money.py").exists():
        errores.append("src/mnfc/money.py ausente")
    bc = ROOT / "src/mnfc/baldor_centimos.py"
    if bc.exists() and "from .money import" not in bc.read_text():
        errores.append("baldor_centimos.py no importa de money.py")


def check_tests():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_cuadre_decimal.py"],
        capture_output=True, text=True, cwd=ROOT,
    )
    if r.returncode != 0:
        errores.append("test_cuadre_decimal.py falló:\n" + r.stdout[-800:])
    else:
        print(f"✅ tests fase 1: {r.stdout.strip().splitlines()[-1]}")


def main():
    print("=" * 60); print("CERTIFICACIÓN — FASE 1 (frontera monetaria)"); print("=" * 60)
    check_schema(); check_codigo(); check_imports(); check_tests()
    if errores:
        print(f"❌ {len(errores)} hallazgo(s). Fase 1: ABIERTA.")
        for e in errores: print(f"   - {e}")
        sys.exit(1)
    import datetime
    print("\n✅ CERTIFICADO EMITIDO — deuda decimal FASE 1 SALDADA.")
    print(f"   Fecha: {datetime.datetime.now().isoformat(timespec='seconds')}")
    print("\nℹ️  Fase 2 (migración de callers) se audita con: python auditar_fase2.py")
    sys.exit(0)


if __name__ == "__main__":
    main()
