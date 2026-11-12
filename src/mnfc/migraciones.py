"""Sistema mínimo de migraciones para SQLite.

Uso:
    from mnfc.migraciones import aplicar_migraciones
    aplicar_migraciones(db_path)

Idempotente: cada migración se aplica una sola vez (registrada en
schema_migrations). Falla con RuntimeError si hay migraciones pendientes
que ya fueron aplicadas en otro orden (checksum).
"""
import sqlite3
import hashlib
from datetime import datetime, timezone
from pathlib import Path


def _checksum(contenido: str) -> str:
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()[:16]


def _versiones_aplicadas(con: sqlite3.Connection) -> dict:
    con.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL, checksum TEXT NOT NULL)"
    )
    con.commit()
    cur = con.execute("SELECT version, checksum FROM schema_migrations")
    return {row[0]: row[1] for row in cur.fetchall()}


def aplicar_migraciones(db_path: str, migrations_dir: str = "migrations") -> list:
    """Aplica migraciones pendientes. Devuelve lista de versiones aplicadas."""
    ruta = Path(migrations_dir)
    if not ruta.exists():
        raise RuntimeError(f"Directorio de migraciones no existe: {migrations_dir}")

    archivos = sorted(ruta.glob("*.sql"))
    con = sqlite3.connect(db_path)
    try:
        aplicadas = _versiones_aplicadas(con)
        pendientes = []
        for f in archivos:
            version = f.stem
            contenido = f.read_text(encoding="utf-8")
            checksum = _checksum(contenido)

            if version in aplicadas:
                if aplicadas[version] != checksum:
                    raise RuntimeError(
                        f"Migración {version} ya aplicada con checksum "
                        f"{aplicadas[version]}, pero el archivo cambió a {checksum}. "
                        "Nunca se edita una migración aplicada."
                    )
                continue

            con.executescript(contenido)
            con.execute(
                "INSERT INTO schema_migrations (version, applied_at, checksum) VALUES (?, ?, ?)",
                (version, datetime.now(timezone.utc).isoformat(), checksum),
            )
            con.commit()
            pendientes.append(version)
        return pendientes
    finally:
        con.close()


def estado(db_path: str, migrations_dir: str = "migrations") -> dict:
    """Devuelve {aplicadas, pendientes, total} sin aplicar nada."""
    ruta = Path(migrations_dir)
    archivos = sorted(ruta.glob("*.sql"))
    total = [f.stem for f in archivos]

    con = sqlite3.connect(db_path)
    try:
        aplicadas = set(_versiones_aplicadas(con).keys())
    except sqlite3.OperationalError:
        aplicadas = set()
    finally:
        con.close()

    return {
        "aplicadas": sorted(aplicadas),
        "pendientes": sorted(set(total) - aplicadas),
        "total": total,
    }
