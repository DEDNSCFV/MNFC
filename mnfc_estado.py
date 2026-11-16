#!/usr/bin/env python3
"""mnfc_estado.py — CLI de la nueva capa (bitácora, hipótesis, Janus)."""
import sys, sqlite3, json
from pathlib import Path

DB = Path(__file__).parent / "nodo_principal_dartony.db"
TABLAS = ['inventario_nodo','stock_por_sucursal','movimientos_dartony',
          'pares_adyacencia','sinopsis_rodriguiana','casos_resueltos',
          'materializaciones','hipotesis_trabajo','ciclos_hitos',
          'libro_folios','bitacora_ventanas','janus_pisos','janus_ast']

def con(): return sqlite3.connect(DB)

def cmd_estado():
    c = con()
    print("═" * 65)
    print("MNFC · ESTADO DE LA BOO")
    print("═" * 65)
    print(f"\nDB: {DB.name} ({DB.stat().st_size:,} bytes)\n")
    print("Tablas:")
    for t in TABLAS:
        try:
            n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t:22s}: {n:>8,}")
        except Exception as e:
            print(f"  {t:22s}: ❌ {e}")

    print("\nÚltimas 5 materializaciones:")
    for r in c.execute("""SELECT materializacion_id, tipo, nombre FROM materializaciones
                          ORDER BY id DESC LIMIT 5"""):
        print(f"  {r[0]:15s} {r[1]:10s} {r[2]}")

    print("\nÚltimos 3 eventos bitácora:")
    for r in c.execute("""SELECT evento_codigo, ventana_id, ecosistema
                          FROM bitacora_ventanas ORDER BY ventana_id DESC, evento_codigo DESC LIMIT 3"""):
        print(f"  {r[0]:8s} {r[1]:12s} {r[2]}")

    print("\nHipótesis PENDIENTES (resolver lunes):")
    for r in c.execute("SELECT codigo, enunciado FROM hipotesis_trabajo WHERE estado='PENDIENTE' ORDER BY codigo"):
        print(f"  {r[0]:10s} {r[1][:55]}")

    print("\nHitos Ciclo 4 pendientes:")
    n = c.execute("SELECT COUNT(*) FROM ciclos_hitos WHERE ciclo=4 AND estado='PENDIENTE'").fetchone()[0]
    print(f"  {n} / 20 en PENDIENTE")
    c.close()

def cmd_bitacora(args):
    c = con()
    if len(args) == 0:
        print(f"{'EV':8s} {'VENTANA':12s} {'ECOSISTEMA':15s} {'TIPO':12s} RESUMEN")
        print("─" * 100)
        for r in c.execute("""SELECT evento_codigo, ventana_id, ecosistema, evento_tipo, resumen
                              FROM bitacora_ventanas ORDER BY ventana_id, evento_codigo"""):
            print(f"{r[0]:8s} {r[1]:12s} {r[2]:15s} {r[3]:12s} {r[4][:45]}")
    else:
        cod = args[0]
        r = c.execute("""SELECT evento_codigo, ventana_id, ecosistema, evento_tipo, resumen,
                         hallazgos, decisiones, pendientes, hash_bitacora
                         FROM bitacora_ventanas WHERE evento_codigo=?""", (cod,)).fetchone()
        if not r: print(f"❌ no existe {cod}"); return
        print(f"\n{r[0]} · {r[1]} · {r[2]} · {r[3]}")
        print(f"\n{r[4]}\n")
        for campo, titulo in [(5,"Hallazgos"),(6,"Decisiones"),(7,"Pendientes")]:
            try:
                items = json.loads(r[campo])
                if items:
                    print(f"{titulo}:")
                    for it in items: print(f"  · {it}")
                    print()
            except: pass
        print(f"sha256:{r[8]}")
    c.close()

def cmd_hipotesis(args):
    c = con()
    solo_pend = "--pendientes" in args
    filtro = "WHERE estado IN ('PENDIENTE','NO_VERIFICABLE')" if solo_pend else ""
    print(f"{'COD':12s} {'ESTADO':16s} {'I (Invariante)'}")
    print("─" * 90)
    for r in c.execute(f"SELECT codigo, estado, invariante FROM hipotesis_trabajo {filtro} ORDER BY codigo"):
        print(f"{r[0]:12s} {r[1]:16s} {r[2] or '—'}")
    c.close()

def cmd_janus(args):
    c = con()
    if not args or args[0] == "pisos":
        print(f"{'COD':6s} {'ORD':4s} {'NOMBRE':28s} FUNCIÓN")
        print("─" * 90)
        for r in c.execute("SELECT codigo, orden, nombre, funcion FROM janus_pisos ORDER BY orden"):
            print(f"{r[0]:6s} {r[1]:>4d} {r[2]:28s} {r[3]}")
    elif args[0] == "ast":
        operador = None
        if "--operador" in args:
            i = args.index("--operador")
            operador = args[i+1] if i+1 < len(args) else None
        if operador:
            rows = c.execute("SELECT operador, linea, texto FROM janus_ast WHERE operador=? LIMIT 20", (operador,)).fetchall()
        else:
            rows = c.execute("""SELECT operador, COUNT(*) FROM janus_ast
                                GROUP BY operador ORDER BY 2 DESC""").fetchall()
        for r in rows: print(f"  {r[0]:20s} {r[1]}")
    c.close()

def cmd_mats():
    c = con()
    print(f"{'MAT_ID':15s} {'TIPO':12s} {'NOMBRE':35s} {'RETRO':5s} HASH")
    print("─" * 100)
    for r in c.execute("""SELECT materializacion_id, tipo, nombre, es_retroactiva, hash_artefacto
                          FROM materializaciones ORDER BY id"""):
        print(f"{r[0]:15s} {r[1]:12s} {r[2]:35s} {'sí' if r[3] else 'no':5s} {(r[4] or '—')[:16]}")
    c.close()

def main():
    args = sys.argv[1:]
    if not args or args[0] == "estado":
        cmd_estado()
    elif args[0] == "bitacora":
        cmd_bitacora(args[1:])
    elif args[0] == "hipotesis":
        cmd_hipotesis(args[1:])
    elif args[0] == "janus":
        cmd_janus(args[1:])
    elif args[0] == "materializaciones":
        cmd_mats()
    else:
        print(__doc__)
        print("Comandos: estado | bitacora [COD] | hipotesis [--pendientes] | janus [pisos|ast] | materializaciones")

if __name__ == "__main__":
    main()
