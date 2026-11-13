# 🏗️ REPORTE INTERNO DE ARQUITECTURA Y MÉTRICAS - MNFC
**Fecha de generación:** 2026-11-13 01:21:59
**Versión del proyecto:** v0.5.0 (Fase 2 Decimal)
**Estado:** Producción / Multi-Tenant
**Evaluador:** Díaz N. Domingo E. (C.P.C. N° 183594)

---

## 1. Métricas de Código (Codebase)
*   **Líneas de código en el núcleo (`src/`):** 5,668 LOC
*   **Líneas de código en pruebas (`tests/`):** 6,184 LOC
*   **Total de líneas auditadas:** 11,852 LOC
*   **Documentación de Arquitectura:** 7 ADRs (Architecture Decision Records)

## 2. Estado de las Pruebas Automatizadas
*   **Resultado de Pytest:** =============== 643/650 tests collected (7 deselected) in 2.82s ================

## 3. Estado de la Base de Datos (Caso Dartony)
*   **Tamaño de la base de datos:** 61.94 MB
*   **SKUs registrados en inventario:** 13,602
*   **Movimientos históricos:** 462,104

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
