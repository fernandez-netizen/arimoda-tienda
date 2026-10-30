import csv
import io
from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# Reemplaza con tu URL CSV de Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQsVyRa9IeaRLCbkeaCGcGL_lOfDbv5kp7SiJNDfIl6mrz5Kz-VaH7LdejqqDop6h1kIE44XNGDMnvE/pub?output=csv"


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
        productos.append({
            "ID": fila_limpia.get("ID", ""),
            "NOMBRE": fila_limpia.get("NOMBRE", ""),
            "DESCRIPCIÓN": fila_limpia.get(
                "DESCRIPCIÓN", fila_limpia.get("DESCRIPCION", "")
            ),
            "PRECIO": fila_limpia.get("PRECIO", "0.00"),
            "URL_IMAGEN": fila_limpia.get("URL_IMAGEN", ""),
            "TALLAS": fila_limpia.get("TALLAS", ""),
            "COLOR": fila_limpia.get("COLOR", ""),
            "ESTOCK": fila_limpia.get("ESTOCK", "SI"),
        })

    return jsonify({"status": "success", "productos": productos})

  except Exception as e:
    print("Error al leer Google Sheets:", e)
    return jsonify({"status": "error", "mensaje": str(e), "productos": []})


if __name__ == "__main__":
  app.run(debug=True)