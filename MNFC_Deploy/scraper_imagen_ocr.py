import pytesseract
from PIL import Image
import re
from decimal import Decimal

def leer_tasas_desde_imagen(ruta_imagen):
    print(f"Procesando imagen: {ruta_imagen}")
    
    # Abrir la imagen y pasarla a texto (OCR)
    imagen = Image.open(ruta_imagen)
    texto_extraido = pytesseract.image_to_string(imagen)
    
    print("--- Texto detectado por la IA ---")
    print(texto_extraido)
    print("---------------------------------")
    
    # Usamos Expresiones Regulares (Regex) para buscar los patrones numéricos
    # Busca números con coma o punto decimal, de 2 a 8 decimales
    patron = re.compile(r'\b\d{1,3}(?:[.,]\d{3})*[.,]\d{2,8}\b')
    numeros_encontrados = patron.findall(texto_extraido)
    
    tasas = {}
    monedas = ["EUR", "CNY", "TRY", "RUB", "USD"]
    
    # Lógica simplificada: asignamos los números encontrados a las monedas
    # (En un sistema real, buscaríamos la palabra "USD" cerca del número)
    print("\nPosibles tasas detectadas:")
    for i, moneda in enumerate(monedas):
        if i < len(numeros_encontrados):
            # Limpiamos el formato (ej. 1.009,34 -> 1009.34)
            valor_limpio = numeros_encontrados[i].replace('.', '').replace(',', '.')
            tasas[moneda] = str(Decimal(valor_limpio))
            print(f"{moneda}: {tasas[moneda]}")

if __name__ == "__main__":
    # Aquí pondrías el nombre de tu captura de pantalla
    # leer_tasas_desde_imagen("captura_bcv.png")
    print("Para probar, guarda tu captura como 'captura_bcv.jpg' y descomenta la línea de arriba.")
