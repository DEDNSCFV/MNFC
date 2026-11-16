"""
Detecta la fuente de datos disponible:
- Si existe dartony_auditoria_v2.db -> modo PC (usa movimiento_historico)
- Si no -> modo Termux (usa movimientos_dartony de la BD motor)
"""
import os
import sqlite3

AUDIT_DB_PC = r"C:\Users\Admin\Desktop\dartony_auditoria_v2.db"
AUDIT_DB_TERMUX = "/sdcard/Download/dartony_auditoria_v2.db"


def get_audit_db_path():
    """Retorna la ruta a la BD de auditoria, o None si no existe."""
    if os.path.exists(AUDIT_DB_PC):
        return AUDIT_DB_PC
    if os.path.exists(AUDIT_DB_TERMUX):
        return AUDIT_DB_TERMUX
    return None


def get_movimientos_source(con):
    """
    Retorna (tabla, columnas_disponibles) para leer movimientos.
    - Si hay BD auditoria -> ('audit.movimiento_historico', [...])
    - Si no -> ('movimientos_dartony', [...])
    """
    audit_db = get_audit_db_path()
    if audit_db:
        return audit_db, "audit.movimiento_historico"
    return None, "movimientos_dartony"


def tiene_movimientos_dartony(con):
    """Verifica si la tabla movimientos_dartony existe en la BD motor."""
    try:
        r = con.execute("SELECT COUNT(*) FROM movimientos_dartony").fetchone()
        return r[0] > 0
    except Exception:
        return False
