import csv
import io
import re
from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# URL CSV de Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQsVyRa9IeaRLCbkeaCGcGL_lOfDbv5kp7SiJNDfIl6mrz5Kz-VaH7LdejqqDop6h1kIE44XNGDMnvE/pub?output=csv"


def procesar_tallas_precios(cadena_tallas, precio_base):
    """
    Parsea cadenas del tipo "L(24), M(22)" o simplemente "S, M, L"
    Retorna una tupla: (lista_de_tallas, diccionario_precios_por_talla)
    """
    if not cadena_tallas:
        return [], {}

    tallas_list = []
    precios_dict = {}

    items = str(cadena_tallas).split(",")
    for item in items:
        item = item.strip()
        if not item:
            continue

        # Busca patrones tipo Talla(Precio), ej: L(24) o XL(25.50)
        match = re.search(r"([A-Za-z0-9]+)\s*\(([\d.]+)\)", item)
        if match:
            talla = match.group(1).upper()
            try:
                precio = float(match.group(2))
            except ValueError:
                precio = float(precio_base) if precio_base else 0.0

            tallas_list.append(talla)
            precios_dict[talla] = precio
        else:
            # Si solo está la talla sin precio entre paréntesis
            talla_simple = item.upper()
            tallas_list.append(talla_simple)
            try:
                precios_dict[talla_simple] = float(precio_base)
            except (ValueError, TypeError):
                precios_dict[talla_simple] = 0.0

    return tallas_list, precios_dict


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/productos")
def obtener_productos():
    try:
        respuesta = requests.get(SHEET_URL)
        respuesta.encoding = "utf-8"

        # Convertir respuesta CSV en diccionario
        f = io.StringIO(respuesta.text)
        lector = csv.DictReader(f)

        productos = []
        for fila in lector:
            # Limpiar espacios en los nombres de las llaves
            fila_limpia = {
                k.strip().upper(): v.strip() for k, v in fila.items() if k
            }

            # Solo agregar si tiene nombre
            if fila_limpia.get("NOMBRE"):
                cadena_tallas = fila_limpia.get("TALLAS", "")
                precio_base = fila_limpia.get("PRECIO", "0.00")

                # Obtener la lista de tallas y el mapa de precios por talla
                tallas_lista, precios_talla_dict = procesar_tallas_precios(
                    cadena_tallas, precio_base
                )

                productos.append({
                    "ID": fila_limpia.get("ID", ""),
                    "NOMBRE": fila_limpia.get("NOMBRE", ""),
                    "DESCRIPCIÓN": fila_limpia.get(
                        "DESCRIPCIÓN", fila_limpia.get("DESCRIPCION", "")
                    ),
                    "PRECIO": precio_base,
                    "URL_IMAGEN": fila_limpia.get("URL_IMAGEN", ""),
                    "TALLAS": cadena_tallas,
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
