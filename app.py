import csv
import io
import re
from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# URL del CSV publicado de tu Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT4g6V4e2s2x8bK9W0J0R7g9J6Q0y5L-9W0e2s2x8bK9W0/pub?output=csv"


def procesar_tallas_precios(cadena_tallas):
    """Parsea una cadena como 'S(24),M(22),L(20)' y extrae:

    - Lista de tallas limpias: ['S', 'M', 'L']
    - Diccionario de precios: {'S': 24.0, 'M': 22.0, 'L': 20.0}
    - Precio inicial por defecto (el de la primera talla)
    """
    if not cadena_tallas:
        return [], {}, 0.0

    tallas_lista = []
    precios_dict = {}

    # Busca patrones tipo TALLA(PRECIO), ej: S(24.50) o M(22)
    items = cadena_tallas.split(",")
    for item in items:
        item = item.strip()
        coincidencia = re.match(r"^([^\(]+)(?:\(([\d\.]+)\))?$", item)
        if coincidencia:
            talla = coincidencia.group(1).strip()
            precio_str = coincidencia.group(2)

            if talla:
                tallas_lista.append(talla)
                if precio_str:
                    try:
                        precios_dict[talla] = float(precio_str)
                    except ValueError:
                        precios_dict[talla] = 0.0
                else:
                    precios_dict[talla] = 0.0

    precio_inicial = 0.0
    if tallas_lista and tallas_lista[0] in precios_dict:
        precio_inicial = precios_dict[tallas_lista[0]]

    return tallas_lista, precios_dict, precio_inicial


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/productos")
def obtener_productos():
    try:
        respuesta = requests.get(SHEET_URL)
        respuesta.encoding = "utf-8"

        f = io.StringIO(respuesta.text)
        lector = csv.DictReader(f)

        productos = []
        for fila in lector:
            # Limpia encabezados y valores de espacios adicionales
            fila_limpia = {
                k.strip().upper(): v.strip() for k, v in fila.items() if k
            }

            if fila_limpia.get("NOMBRE"):
                cadena_tallas = fila_limpia.get("TALLAS", "")

                tallas_lista, precios_talla_dict, precio_inicial = (
                    procesar_tallas_precios(cadena_tallas)
                )

                # Acepta tanto ESTOCK como STOCK en Google Sheets
                val_stock = (
                    fila_limpia.get("ESTOCK")
                    or fila_limpia.get("STOCK")
                    or "SI"
                )

                productos.append({
                    "ID": fila_limpia.get("ID", ""),
                    "NOMBRE": fila_limpia.get("NOMBRE", ""),
                    "DESCRIPCIÓN": fila_limpia.get(
                        "DESCRIPCIÓN", fila_limpia.get("DESCRIPCION", "")
                    ),
                    "PRECIO": precio_inicial,
                    "URL_IMAGEN": fila_limpia.get("URL_IMAGEN", ""),
                    "TALLAS": ",".join(tallas_lista),
                    "tallas_lista": tallas_lista,
                    "precios_talla": precios_talla_dict,
                    "COLOR": fila_limpia.get("COLOR", ""),
                    "ESTOCK": val_stock,
                })

        return jsonify({"status": "success", "productos": productos})

    except Exception as e:
        print("Error al leer Google Sheets:", e)
        return jsonify({"status": "error", "mensaje": str(e), "productos": []})


if __name__ == "__main__":
    app.run(debug=True)
