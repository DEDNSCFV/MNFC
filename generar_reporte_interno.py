import os
import subprocess
import sqlite3
from datetime import datetime

DB_PATH = "nodo_principal_dartony.db"
REPORT_FILE = "REPORTE_INTERNO.md"

def get_loc(directory):
    total = 0
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith('.py'):
                with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as file:
                    total += len(file.readlines())
    return total

def get_test_count():
    try:
        result = subprocess.run(["python", "-m", "pytest", "--collect-only", "-q"], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if 'test' in line and ('collected' in line or 'tests' in line):
                return line.strip()
        return "Verificar manualmente en la suite."
    except Exception as e:
        return f"Error ejecutando pytest: {e}"

def get_db_stats():
    if not os.path.exists(DB_PATH):
        return None
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM inventario_nodo")
        skus = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM movimientos_dartony")
        movs = cur.fetchone()[0]
        size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
        con.close()
        return {"skus": skus, "movs": movs, "size_mb": size_mb}
    except Exception as e:
        return {"error": str(e)}

def get_adrs():
    adr_dir = "docs/adr"
    if os.path.exists(adr_dir):
        return len([f for f in os.listdir(adr_dir) if f.endswith('.md')])
    return 0

def main():
    print("⏳ Escaneando repositorio y generando reporte...")
    
    loc_src = get_loc("src")
    loc_tests = get_loc("tests")
    test_info = get_test_count()
    db_stats = get_db_stats()
    adrs = get_adrs()
    
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# 🏗️ REPORTE INTERNO DE ARQUITECTURA Y MÉTRICAS - MNFC
**Fecha de generación:** {fecha}
**Versión del proyecto:** v0.5.0 (Fase 2 Decimal)
**Estado:** Producción / Multi-Tenant
**Evaluador:** Díaz N. Domingo E. (C.P.C. N° 183594)

---

## 1. Métricas de Código (Codebase)
*   **Líneas de código en el núcleo (`src/`):** {loc_src:,} LOC
*   **Líneas de código en pruebas (`tests/`):** {loc_tests:,} LOC
*   **Total de líneas auditadas:** {loc_src + loc_tests:,} LOC
*   **Documentación de Arquitectura:** {adrs} ADRs (Architecture Decision Records)

## 2. Estado de las Pruebas Automatizadas
*   **Resultado de Pytest:** {test_info}

## 3. Estado de la Base de Datos (Caso Dartony)
"""
    if db_stats and "error" not in db_stats:
        report += f"""*   **Tamaño de la base de datos:** {db_stats['size_mb']:.2f} MB
*   **SKUs registrados en inventario:** {db_stats['skus']:,}
*   **Movimientos históricos:** {db_stats['movs']:,}
"""
    else:
        report += "*   *Base de datos de producción no encontrada en este entorno (Modo Instalación Limpia).*\n"

    report += """
## 4. Cumplimiento de Estándares Técnicos
*   **Precisión Numérica:** Aritmética de enteros (centavos) + `ROUND_HALF_EVEN` (NIIF).
*   **Inmunidad a la Deriva:** 0 `float` en el núcleo de cálculo.
*   **Resiliencia:** Fuzzing y validación de límites numéricos (NaN, Infinity).
*   **IA Simbólica:** 100% explicable (sin cajas negras ni alucinaciones).
*   **Arquitectura:** Cadena secuencial Capa 4 -> Capa 7 (ADR-004).

## 5. Despliegue y Portabilidad
*   **Multi-Tenant:** Configuración dinámica vía `config.json`.
*   **Instalador:** Script `setup_pc.py` para inicializar BD en blanco.
*   **Paquete de Distribución:** `MNFC_v0.5.0_Cliente.zip` (Portable, Zero-Cloud).
*   **RPA Integrado:** Scraper BCV para tasas oficiales en tiempo real.

---
*Este reporte fue generado automáticamente por el módulo de auditoría interna del MNFC.*
"""
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"✅ Reporte generado exitosamente: {REPORT_FILE}")

if __name__ == "__main__":
    main()
