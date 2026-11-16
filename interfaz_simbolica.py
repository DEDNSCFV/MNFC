#!/usr/bin/env python3
"""
interfaz_simbolica.py — Motor de verificación del programa SCFV.

NO es un agente. NO decide. Verifica contra contrato y reporta.

Uso:
    python3 interfaz_simbolica.py boot              # verifica y sale
    python3 interfaz_simbolica.py boot --instruccion "cargar AM0"
    python3 interfaz_simbolica.py historial         # sesiones previas
"""
import sys, sqlite3, json, hashlib
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
DB = BASE / "nodo_principal_dartony.db"
CONTRATO = BASE / "interfaz_contrato.json"
OPERADOR = "Domingo E. Díaz N. (C.P.C. 183594)"

def query_real():
    """Consulta el estado real de la BD."""
    con = sqlite3.connect(DB)
    real = {"tablas": {}}
    for t in ["bitacora_ventanas","hipotesis_trabajo","ciclos_hitos",
              "janus_pisos","janus_ast","materializaciones","libro_folios"]:
        try:
            real["tablas"][t] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception:
            real["tablas"][t] = None
    real["hipotesis_pendientes"] = [r[0] for r in con.execute(
        "SELECT codigo FROM hipotesis_trabajo WHERE estado IN ('PENDIENTE','NO_VERIFICABLE') ORDER BY codigo")]
    real["hitos_ciclo4_pendientes"] = con.execute(
        "SELECT COUNT(*) FROM ciclos_hitos WHERE ciclo=4 AND estado='PENDIENTE'").fetchone()[0]
    r = con.execute("SELECT evento_codigo FROM bitacora_ventanas ORDER BY ventana_id DESC, evento_codigo DESC LIMIT 1").fetchone()
    real["ultimo_evento_bitacora"] = r[0] if r else None
    con.close()
    return real

def comparar(esperado, real):
    gaps = []
    # Tablas
    for t, spec in esperado["tablas"].items():
        actual = real["tablas"].get(t)
        if spec["tolerancia"] == "exacto":
            if actual != spec["count"]:
                gaps.append(f"tabla {t}: esperado={spec['count']} real={actual}")
        elif spec["tolerancia"] == "minimo":
            if actual is None or actual < spec["count"]:
                gaps.append(f"tabla {t}: esperado>={spec['count']} real={actual}")
    # Hipótesis pendientes
    if sorted(esperado["hipotesis_pendientes"]) != sorted(real["hipotesis_pendientes"]):
        gaps.append(f"hipotesis_pendientes: esperado={esperado['hipotesis_pendientes']} real={real['hipotesis_pendientes']}")
    # Hitos
    if esperado["hitos_ciclo4_pendientes"] != real["hitos_ciclo4_pendientes"]:
        gaps.append(f"hitos_ciclo4_pendientes: esperado={esperado['hitos_ciclo4_pendientes']} real={real['hitos_ciclo4_pendientes']}")
    # Último evento
    if esperado["ultimo_evento_bitacora"] != real["ultimo_evento_bitacora"]:
        gaps.append(f"ultimo_evento: esperado={esperado['ultimo_evento_bitacora']} real={real['ultimo_evento_bitacora']}")
    return gaps

def registrar_sesion(estado, gaps, instruccion, accion):
    con = sqlite3.connect(DB)
    hora = datetime.now().isoformat(timespec="seconds")
    sid = f"SES-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    payload = json.dumps({"sid": sid, "estado": estado, "gaps": gaps, "hora": hora}, sort_keys=True)
    h = hashlib.sha256(payload.encode()).hexdigest()[:32]
    con.execute("""INSERT OR IGNORE INTO interfaz_sesiones
        (sesion_id, hora, operador, contrato_ver, estado_real, gaps,
         instruccion, accion_tomada, hash_sesion)
        VALUES (?,?,?,?,?,?,?,?,?)""", (
        sid, hora, OPERADOR, "1.0", estado,
        json.dumps(gaps, ensure_ascii=False),
        instruccion or "", accion or "", h))
    con.commit()
    con.close()
    return sid

def cmd_boot(args):
    instruccion = ""
    if "--instruccion" in args:
        i = args.index("--instruccion")
        instruccion = args[i+1] if i+1 < len(args) else ""

    print("═" * 65)
    print("INTERFAZ SIMBÓLICA · SCFV / Nodo Dartony")
    print("═" * 65)

    contrato = json.loads(CONTRATO.read_text(encoding="utf-8"))
    print(f"\nContrato: v{contrato['version']} · {contrato['generado_en']}")
    print(f"Operador: {contrato['operador']}")
    if instruccion:
        print(f"Instrucción: {instruccion}")

    real = query_real()
    print(f"\nConsultando BD... ({DB.stat().st_size:,} bytes)")

    gaps = comparar(contrato["esperado"], real)

    if gaps:
        print("\n❌ DETENIDA — el estado no coincide con el contrato\n")
        for g in gaps:
            print(f"   · {g}")
        print(f"\nAcción prescrita: {contrato['si_no_cuadra']['accion']}")
        print(f"Razón: {contrato['si_no_cuadra']['razon']}")
        print(f"Qué hacer: {contrato['si_no_cuadra']['que_hacer']}")
        sid = registrar_sesion("DETENIDA", gaps, instruccion, "DETENIDA")
        print(f"\nSesión registrada: {sid}")
        return 1
    else:
        print("\n✅ OK — el estado coincide con el contrato\n")
        print("   Tablas verificadas:")
        for t, spec in contrato["esperado"]["tablas"].items():
            print(f"     · {t:22s}: {real['tablas'][t]} ({spec['tolerancia']})")
        print(f"   Hipótesis pendientes: {real['hipotesis_pendientes']}")
        print(f"   Último evento: {real['ultimo_evento_bitacora']}")
        print(f"\n   Procede con: {instruccion or '[instrucción del operador]'}")
        sid = registrar_sesion("OK", [], instruccion, "PERMITIDA")
        print(f"\nSesión registrada: {sid}")
        return 0

def cmd_historial(args):
    con = sqlite3.connect(DB)
    print(f"{'SESION_ID':22s} {'HORA':20s} {'ESTADO':10s} GAPS")
    print("─" * 90)
    for r in con.execute("""SELECT sesion_id, hora, estado_real, gaps
                            FROM interfaz_sesiones ORDER BY id DESC LIMIT 20"""):
        try:
            n = len(json.loads(r[3])) if r[3] else 0
        except: n = 0
        print(f"{r[0]:22s} {r[1]:20s} {r[2]:10s} {n} gap(s)")
    con.close()

def main():
    args = sys.argv[1:]
    if not args or args[0] == "boot":
        sys.exit(cmd_boot(args[1:]))
    elif args[0] == "historial":
        cmd_historial(args[1:])
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
