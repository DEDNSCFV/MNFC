#!/usr/bin/env python3
"""Lee bitacoras/eventos_*.json, crea tabla, inserta, genera MD."""
import sqlite3, hashlib, json
from pathlib import Path
from datetime import datetime

OPERADOR = "Domingo E. Díaz N. (C.P.C. 183594)"
DB = "nodo_principal_dartony.db"
EVENTOS_JSON = Path("bitacoras/eventos_2026-11-15.json")

con = sqlite3.connect(DB)
con.executescript("""
CREATE TABLE IF NOT EXISTS bitacora_ventanas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ventana_id TEXT NOT NULL, evento_codigo TEXT NOT NULL,
    ciclo TEXT NOT NULL, ecosistema TEXT NOT NULL, evento_tipo TEXT NOT NULL,
    operador TEXT NOT NULL, inicio TEXT NOT NULL, fin TEXT, duracion_min INTEGER,
    resumen TEXT, hallazgos TEXT, correcciones TEXT, decisiones TEXT, pendientes TEXT,
    archivos TEXT, estado_pendiente TEXT, hito_proximo TEXT,
    hash_bitacora TEXT NOT NULL, creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ventana_id, evento_codigo)
);
CREATE INDEX IF NOT EXISTS idx_bv_ciclo ON bitacora_ventanas(ciclo);
CREATE INDEX IF NOT EXISTS idx_bv_eco   ON bitacora_ventanas(ecosistema);
""")
print("✅ tabla lista")

eventos = json.loads(EVENTOS_JSON.read_text(encoding="utf-8"))
print(f"✅ {len(eventos)} eventos leídos del JSON")

for ev in eventos:
    payload = json.dumps({k: ev.get(k) for k in ev if k not in ("ventana_id","evento_codigo")},
                         sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256(payload.encode()).hexdigest()
    con.execute("""INSERT OR REPLACE INTO bitacora_ventanas
        (ventana_id,evento_codigo,ciclo,ecosistema,evento_tipo,operador,inicio,fin,
         duracion_min,resumen,hallazgos,correcciones,decisiones,pendientes,archivos,
         estado_pendiente,hito_proximo,hash_bitacora)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        ev["ventana_id"], ev["evento_codigo"], ev["ciclo"], ev["ecosistema"],
        ev["evento_tipo"], OPERADOR, ev["inicio"], ev.get("fin"), ev.get("duracion_min"),
        ev["resumen"],
        json.dumps(ev.get("hallazgos",[]), ensure_ascii=False),
        json.dumps(ev.get("correcciones",[]), ensure_ascii=False),
        json.dumps(ev.get("decisiones",[]), ensure_ascii=False),
        json.dumps(ev.get("pendientes",[]), ensure_ascii=False),
        json.dumps(ev.get("archivos",[]), ensure_ascii=False),
        ev.get("estado_pendiente",""), ev.get("hito_proximo",""), h,
    ))
con.commit()
n = con.execute("SELECT COUNT(*) FROM bitacora_ventanas").fetchone()[0]
print(f"✅ {n} eventos en bitacora_ventanas")

# MD oficial
md = [f"# Bitácora — SCFV / Nodo Dartony\n", f"*Generado: {datetime.now().isoformat(timespec='seconds')}*\n", f"*Operador: {OPERADOR}*\n\n---\n"]
for eco in ["MNFC", "SCFV_DARTONY"]:
    rows = con.execute("""SELECT ventana_id,evento_codigo,evento_tipo,resumen,hallazgos,
        correcciones,decisiones,pendientes,estado_pendiente,hito_proximo,hash_bitacora
        FROM bitacora_ventanas WHERE ecosistema=? ORDER BY ventana_id""", (eco,)).fetchall()
    if not rows: continue
    md.append(f"\n## Ecosistema {eco}\n")
    for r in rows:
        md.append(f"\n### {r[1]} · {r[0]} · {r[2]}\n\n{r[3]}\n")
        for idx, tit in [(4,"Hallazgos"),(5,"Correcciones"),(6,"Decisiones"),(7,"Pendientes")]:
            try:
                items = json.loads(r[idx])
                if items:
                    md.append(f"\n**{tit}:**")
                    for it in items: md.append(f"- {it}")
            except: pass
        if r[8]: md.append(f"\n**Estado pendiente:** {r[8]}")
        if r[9]: md.append(f"  \n**Próximo hito:** {r[9]}")
        md.append(f"\n`sha256:{r[10][:16]}...`")

texto = "\n".join(md)
h = hashlib.sha256(texto.encode()).hexdigest()
Path("bitacoras/2026-11-15_ventana.md").write_text(texto + f"\n\n## Hash de esta bitácora\n`sha256:{h}`\n", encoding="utf-8")
print(f"✅ bitacoras/2026-11-15_ventana.md ({len(texto):,} chars)  sha256:{h[:16]}...")

print("\n=== Distribución ===")
for r in con.execute("SELECT ecosistema, COUNT(*) FROM bitacora_ventanas GROUP BY ecosistema"):
    print(f"  {r[0]:18s}: {r[1]}")
for r in con.execute("SELECT evento_tipo, COUNT(*) FROM bitacora_ventanas GROUP BY evento_tipo"):
    print(f"  {r[0]:18s}: {r[1]}")
r = con.execute("SELECT MIN(ventana_id), MAX(ventana_id) FROM bitacora_ventanas").fetchone()
print(f"  Rango: {r[0]} → {r[1]}")
con.close()
