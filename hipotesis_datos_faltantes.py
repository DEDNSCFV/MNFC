#!/usr/bin/env python3
"""
Registra las 3 hipótesis sobre datos faltantes como artefacto inmutable.
Cada hipótesis tiene: predicción, criterio de confirmación, criterio de refutación.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

OUT = Path.home() / "DARTONY_TXT"
OUT.mkdir(parents=True, exist_ok=True)
FECHA = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

hipotesis = {
    "fecha_registro": FECHA,
    "autor": "Domingo E. Díaz N. | C.P.C. N.º 183594",
    "proposito": "Registrar predicciones falsables sobre datos faltantes antes de cargarlos",
    "principio_epistemologico": "Una hipótesis es científica si puede ser refutada. Estas 3 hipótesis predicen qué pasará cuando se carguen los datos faltantes. Si los resultados caen fuera de los rangos predichos, las hipótesis se refutan y hay que revisar el modelo.",
    "estado_actual": {
        "nodos_con_datos": ["01 Central", "04 La Urbina", "05 Cúa", "06 TERE"],
        "nodos_sin_datos": ["08 Charallave", "La Raiza", "Palo Verde"],
        "periodo_analizado": "Feb 2026 - Sep 2026",
        "movimientos_en_db": 462104,
        "movimientos_con_trazabilidad_fila": 225049,
        "brecha_temporal": "kardex a agosto, stock a octubre (2 meses de desfase)"
    },
    "hipotesis": [
        {
            "id": "H1",
            "nombre": "Sobre Central (datos presentes, sin trazabilidad de fila)",
            "prediccion": "Cuando se cargue el TXT de Central, los resultados de las 14 reglas se mantendrán exactamente iguales.",
            "predicciones_cuantitativas": {
                "total_movimientos_esperados": 237055,
                "regla_7": "573/54,220 (1.1%)",
                "regla_9": "1,625/6,946 (23.4%)",
                "regla_12": "158,421 NENT / 14,515 NREC (10.9x)",
                "regla_13": "4,125 ajustes >$500"
            },
            "criterio_confirmacion": "Parser extrae exactamente 237,055 movimientos y el conteo por tipo coincide al 100% con movimientos_historico",
            "criterio_refutacion": "Parser extrae menos de 237,055 movimientos o el conteo por tipo no coincide",
            "implicacion_si_confirma": "Trazabilidad de fila de Central queda demostrada. La DB queda validada contra su fuente.",
            "implicacion_si_refuta": "La DB está inflada con movimientos que no están en el TXT fuente. Todas las cifras de Central son sospechosas."
        },
        {
            "id": "H2",
            "nombre": "Sobre los 3 nodos ausentes",
            "prediccion": "Cuando se extraigan Charallave, La Raiza y Palo Verde, el fill rate bajará, el ratio NENT/NREC se mantendrá, y la rotación bajará.",
            "predicciones_cuantitativas": {
                "fill_rate_actual": "93.7%",
                "fill_rate_predicho": "90-92%",
                "ratio_nent_nrec_actual": "10.9x",
                "ratio_nent_nrec_predicho": "10.5-11.0x",
                "rotacion_actual": "8.83x",
                "rotacion_predicha": "7.0-8.0x",
                "dias_inventario_actual": "41 días",
                "dias_inventario_predichos": "46-52 días"
            },
            "razonamiento": {
                "fill_rate_baja": "Los 3 nodos faltantes probablemente tienen peor desempeño que Central (1.1%) y La Urbina (5.1%)",
                "ratio_se_mantiene": "Según el PDF, solo Central emite NENT. Los otros nodos solo reciben NREC.",
                "rotacion_baja": "Los 3 nodos agregarán inventario al denominador pero probablemente menos ventas proporcionalmente"
            },
            "criterio_confirmacion": "Los 3 KPIs caen dentro de los rangos predichos",
            "criterio_refutacion": "Algún KPI cae fuera del rango. Por ejemplo, fill rate sube a 95%.",
            "implicacion_si_confirma": "El modelo predictivo es correcto. Los 3 nodos faltantes son de menor desempeño.",
            "implicacion_si_refuta": "El modelo estaba mal. Los 3 nodos faltantes tienen mejor desempeño del esperado, o la estructura de la empresa es distinta."
        },
        {
            "id": "H3",
            "nombre": "Sobre el desfase temporal (sept-oct)",
            "prediccion": "Cuando se carguen los movimientos de septiembre y octubre al kardex, la diferencia entre stock_central y movimientos_sep.stock_final se reducirá de 13,958 unidades a menos de 2,000.",
            "predicciones_cuantitativas": {
                "diferencia_actual": "13,958 unidades",
                "diferencia_predicha": "< 2,000 unidades",
                "movimientos_faltantes": "77,322 (septiembre + octubre)"
            },
            "razonamiento": "La diferencia actual se explica por los 77,322 movimientos de sept-oct que no están en el kardex. Al cargarlos, la diferencia debería casi desaparecer.",
            "criterio_confirmacion": "Diferencia baja a < 2,000 unidades",
            "criterio_refutacion": "Diferencia sigue siendo > 5,000 unidades después de cargar sept-oct",
            "implicacion_si_confirma": "El desfase temporal era la causa principal. No hay problema de registro.",
            "implicacion_si_refuta": "El desfase no era la causa principal. Hay un problema de fondo en el registro del kardex."
        }
    ],
    "protocolo_validacion": {
        "paso_1": "Cargar los datos faltantes (TXT de Central, 3 nodos, sept-oct)",
        "paso_2": "Ejecutar el mismo evaluador sobre el corpus ampliado",
        "paso_3": "Comparar cada KPI con la predicción correspondiente",
        "paso_4": "Registrar si la hipótesis se confirmó o se refutó",
        "paso_5": "Si se refutó, revisar el modelo y registrar por qué falló",
        "paso_6": "Emitir V002 de los libros con los datos completos y el resultado de las hipótesis"
    },
    "principio_de_inmutabilidad": "Este archivo se registra con hash SHA256. Cualquier modificación posterior rompe la cadena. Las hipótesis se registran ANTES de cargar los datos, para que no puedan ajustarse a los resultados."
}

archivo = OUT / f"hipotesis_datos_faltantes_{FECHA.replace(':','').replace('-','')}.json"
with open(archivo, 'w', encoding='utf-8') as f:
    json.dump(hipotesis, f, indent=2, ensure_ascii=False)

with open(archivo, 'rb') as f:
    h = hashlib.sha256(f.read()).hexdigest()

# Registrar el hash en un archivo aparte (cadena de inmutabilidad)
registro = OUT / "cadena_hipotesis.txt"
with open(registro, 'a', encoding='utf-8') as f:
    f.write(f"{FECHA} | {archivo.name} | SHA256: {h}\n")

print(f"Hipótesis registradas: {archivo.name}")
print(f"SHA256: {h}")
print()
print("=== HIPÓTESIS REGISTRADAS ===")
for hip in hipotesis["hipotesis"]:
    print(f"  {hip['id']} — {hip['nombre']}")
    print(f"       Predicción: {hip['prediccion'][:80]}...")
    print()
print(f"Registro de cadena: {registro}")
print()
print("IMPORTANTE: estas hipótesis se registran ANTES de cargar los datos.")
print("Si los resultados futuros no coinciden, las hipótesis se refutan.")
print("Eso es lo que las hace científicas: pueden fallar.")
