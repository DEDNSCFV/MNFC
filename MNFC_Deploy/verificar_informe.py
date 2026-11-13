import hashlib
import sqlite3
from pathlib import Path

DB = Path.home() / "dartony_auditoria.db"
ARCHIVO = Path.home() / "INFORME_DIARIO_DARTONY_2026-11-08.md"

# 1. Leer el archivo actual y calcular su hash
texto_actual = ARCHIVO.read_text(encoding='utf-8')
hash_actual = hashlib.sha256(texto_actual.encode('utf-8')).hexdigest()

# 2. Buscar el hash original en la base de datos
con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("SELECT hash_firma FROM firma_auditor ORDER BY id DESC LIMIT 1")
resultado = cur.fetchone()
hash_original = resultado[0] if resultado else "NO_ENCONTRADO"
con.close()

# 3. Comparar
print(f"Hash Original (BD):  {hash_original}")
print(f"Hash Actual (Archivo): {hash_actual}")
print("-" * 60)

if hash_actual == hash_original:
    print("✅ INTEGRIDAD VERIFICADA: El documento no ha sido alterado.")
else:
    print("🚨 ALERTA DE AUDITORÍA: ¡El documento ha sido manipulado!")
    print("   El sello criptográfico no coincide. El informe ya no es válido.")
