import json
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
import urllib3

# Desactivar warnings de SSL para Termux
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def limpiar_formato_bcv(texto):
    """
    Limpia el formato numérico del BCV (Ej: 1.009,34 -> 1009.34).
    Remueve espacios y maneja puntos de miles y comas decimales.
    """
    texto = texto.strip().replace('\xa0', '').replace(' ', '')
    
    if ',' in texto and '.' in texto:
        # Formato 1.009,34 -> Quitar punto de miles, cambiar coma por punto
        texto = texto.replace('.', '').replace(',', '.')
    elif ',' in texto:
        # Formato 911,62 -> Solo cambiar coma por punto
        texto = texto.replace(',', '.')
    
    return texto

def extraer_tasas_bcv():
    url = "https://www.bcv.org.ve/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print("Conectando al BCV...")
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    monedas = {
        "USD": "dolar",
        "EUR": "euro",
        "CNY": "yuan",
        "TRY": "lira",
        "RUB": "rublo"
    }
    
    tasas = {}
    print("-" * 40)
    for moneda, id_html in monedas.items():
        div = soup.find('div', id=id_html)
        if div and div.find('strong'):
            valor_sucio = div.find('strong').text
            valor_limpio = limpiar_formato_bcv(valor_sucio)
            
            try:
                # Validamos que sea un número exacto antes de guardarlo
                tasa_decimal = Decimal(valor_limpio)
                tasas[moneda] = str(tasa_decimal)
                print(f"✅ Tasa {moneda}: {tasa_decimal}")
            except Exception as e:
                print(f"⚠️ Error al parsear {moneda}: '{valor_sucio}' -> {e}")
        else:
            print(f"⚠️ No se encontró la moneda {moneda}")

    # Guardar en JSON para que el MNFC lo consuma
    if tasas:
        with open("tasas_bcv.json", "w") as f:
            json.dump(tasas, f, indent=4)
        print("-" * 40)
        print("✅ Todas las tasas guardadas en 'tasas_bcv.json'")

if __name__ == "__main__":
    extraer_tasas_bcv()
