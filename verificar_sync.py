#!/usr/bin/env python3
"""verificar_sync.py — Termux (BOO) recibe y valida sync desde PC (BOM).
Uso: python3 verificar_sync.py --auto
     python3 verificar_sync.py <sync.db> <sync.manifest.json>
"""
import sys, json, sqlite3, hashlib
from pathlib import Path

BOO = Path(__file__).parent / "nodo_principal_dartony.db"
INCOMING = Path(__file__).parent / "incoming"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def tabla_cols(con, tabla):
    return [r[1] for r in con.execute(f"PRAGMA table_info({tabla})")]

def merge(db_sync, manifest):
    print(f"\n📦 {db_sync.name}  ({db_sync.stat().st_size:,} bytes)")
    real = sha256(db_sync)
    ok_hash = real == manifest["sync_hash"]
    print(f"   hash manifest: {manifest['sync_hash'][:16]}...")
    print(f"   hash real    : {real[:16]}...  {'✅' if ok_hash else '❌ MISMATCH'}")
    if not ok_hash: return False

    src = sqlite3.connect(db_sync)
    dst = sqlite3.connect(BOO)
    ok = True
    for tabla, info in manifest["tablas"].items():
        try:
            n_src = src.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        except Exception as e:
            print(f"   ❌ {tabla}: {e}"); ok = False; continue
        if n_src != info["filas"]:
            print(f"   ⚠️  {tabla}: manifest={info['filas']:,} real={n_src:,}")
            ok = False
        cols_src = set(tabla_cols(src, tabla))
        cols_dst = set(tabla_cols(dst, tabla))
        comunes = sorted(cols_src & cols_dst)
        if not comunes:
            print(f"   ❌ {tabla}: sin columnas comunes"); ok = False; continue
        cols = ",".join(comunes)
        ph = ",".join(["?"] * len(comunes))
        rows = src.execute(f"SELECT {cols} FROM {tabla}").fetchall()
        dst.executemany(f"INSERT OR REPLACE INTO {tabla} ({cols}) VALUES ({ph})", rows)
        print(f"   ✅ {tabla:25s}: {len(rows):>8,} filas merged")
    dst.commit()
    print("\n   --- post-merge ---")
    for tabla in manifest["tablas"]:
        n = dst.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"   {tabla:25s}: {n:>8,} filas en BOO")
    src.close(); dst.close()
    return ok

def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--auto":
        if not INCOMING.exists():
            print(f"❌ falta {INCOMING}/"); sys.exit(1)
        dbs = sorted(INCOMING.glob("sync_bom_*.db"))
        if not dbs: print("❌ sin .db"); sys.exit(1)
        db = dbs[-1]
        man = db.with_suffix(".manifest.json")
        if not man.exists(): print(f"❌ falta {man.name}"); sys.exit(1)
        manifest = json.loads(man.read_text(encoding="utf-8"))
    elif len(sys.argv) == 3:
        db = Path(sys.argv[1])
        manifest = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    else:
        print(__doc__); sys.exit(1)
    sys.exit(0 if merge(db, manifest) else 2)

if __name__ == "__main__":
    main()
