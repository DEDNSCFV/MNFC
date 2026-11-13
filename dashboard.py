import sqlite3
import json
from decimal import Decimal
from flask import Flask, render_template_string, jsonify
from mnfc.money import to_decimal

app = Flask(__name__)
DB_PATH = "nodo_principal_dartony.db"

# Plantilla HTML (Interfaz visual)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MNFC - Panel del CPC</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; color: #333; }
        .header { background: #1a365d; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        h2 { color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #e2e8f0; }
        th { background-color: #edf2f7; }
        .badge-alta { background: #fed7d7; color: #9b2c2c; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
        .badge-media { background: #fefcbf; color: #975a16; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .kpi { font-size: 2em; color: #2b6cb0; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ MNFC - Panel de Control del CPC</h1>
        <p>Evaluador: Díaz N. Domingo E. | C.P.C. N° 183594</p>
    </div>

    <div class="grid-2">
        <div class="card">
            <h2>📦 Inventario Valorizado</h2>
            <table>
                <tr><th>SKU</th><th>Cant.</th><th>Costo (Bs)</th></tr>
                {% for p in inventario %}
                <tr>
                    <td>{{ p[0] }}</td>
                    <td>{{ p[1] }}</td>
                    <td>{{ p[2] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="card">
            <h2>🚨 Hallazgos de Auditoría</h2>
            <table>
                <tr><th>Tipo</th><th>Severidad</th><th>Descripción</th></tr>
                {% for h in hallazgos %}
                <tr>
                    <td>{{ h[0] }}</td>
                    <td><span class="badge-{{ 'alta' if h[1] == 'ALTA' else 'media' }}">{{ h[1] }}</span></td>
                    <td style="font-size: 0.9em;">{{ h[2] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>

    <div class="card" style="text-align: center;">
        <h2>📊 Rotación del Inventario</h2>
        <div class="kpi">{{ rotacion }}</div>
        <p>Veces en los últimos 30 días</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Datos de Inventario
    cur.execute("SELECT sku, cantidad_fisica, costo_unitario_cent FROM inventario_nodo")
    inv_raw = cur.fetchall()
    inventario = [(r[0], r[1], to_decimal(r[2])) for r in inv_raw]

    # Datos de Hallazgos
    cur.execute("SELECT tipo, severidad, descripcion FROM hallazgos_auditoria ORDER BY id DESC")
    hallazgos = cur.fetchall()

    # KPI de Rotación (simplificado para la vista)
    rotacion = "0.03" 

    con.close()
    return render_template_string(HTML_TEMPLATE, inventario=inventario, hallazgos=hallazgos, rotacion=rotacion)

if __name__ == '__main__':
    print("Iniciando servidor MNFC en http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
