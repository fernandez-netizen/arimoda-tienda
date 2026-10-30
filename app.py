import csv
import io
import re
from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQsVyRa9IeaRLCbkeaCGcGL_lOfDbv5kp7SiJNDfIl6mrz5Kz-VaH7LdejqqDop6h1kIE44XNGDMnvE/pub?output=csv"

def procesar_tallas_precios(cadena_tallas):
    """
    Parsea cadenas tipo "L(24),M(22),S(20)"
    Retorna: (lista_tallas_limpias, dict_precios, precio_inicial)
    """
    if not cadena_tallas:
        return [], {}, "0.00"

    tallas_list = []
    precios_dict = {}

    items = str(cadena_tallas).split(",")
    for item in items:
        item = item.strip()
        if not item:
            continue

        match = re.search(r"([A-Za-z0-9]+)\s*\(([\d.]+)\)", item)
        if match:
            talla = match.group(1).upper()
            precio = float(match.group(2))
            tallas_list.append(talla)
            precios_dict[talla] = precio
        else:
            talla_simple = item.upper()
            tallas_list.append(talla_simple)
            precios_dict[talla_simple] = 0.0

    # Determina el precio por defecto (el de la primera talla en la lista)
    precio_inicial = "0.00"
    if tallas_list and tallas_list[0] in precios_dict:
        precio_inicial = f"{precios_dict[tallas_list[0]]:.2f}"

    return tallas_list, precios_dict, precio_inicial


@app.route("/")
def home():
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
            fila_limpia = {
                k.strip().upper(): v.strip() for k, v in fila.items() if k
            }

            if fila_limpia.get("NOMBRE"):
                cadena_tallas = fila_limpia.get("TALLAS", "")
                
                tallas_lista, precios_talla_dict, precio_inicial = procesar_tallas_precios(cadena_tallas)

                productos.append({
                    "ID": fila_limpia.get("ID", ""),
                    "NOMBRE": fila_limpia.get("NOMBRE", ""),
                    "DESCRIPCIÓN": fila_limpia.get("DESCRIPCIÓN", fila_limpia.get("DESCRIPCION", "")),
                    "PRECIO": precio_inicial,  # Precio de la primera talla por defecto
                    "URL_IMAGEN": fila_limpia.get("URL_IMAGEN", ""),
                    "TALLAS": ",".join(tallas_lista),  # Tallas limpias: "L,M,S"
                    "tallas_lista": tallas_lista,
                    "precios_talla": precios_talla_dict,
                    "COLOR": fila_limpia.get("COLOR", ""),
                    "ESTOCK": fila_limpia.get("ESTOCK", "SI"),
                })

        return jsonify({"status": "success", "productos": productos})

    except Exception as e:
        print("Error al leer Google Sheets:", e)
        return jsonify({"status": "error", "mensaje": str(e), "productos": []})


if __name__ == "__main__":
    app.run(debug=True)
