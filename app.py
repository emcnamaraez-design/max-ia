# app.py - Version diagnostica
import sys
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Intentar importar el agente y capturar cualquier error
try:
    from agente_vendedor import procesar_mensaje
    IMPORT_ERROR = None
except Exception as e:
    IMPORT_ERROR = traceback.format_exc()
    procesar_mensaje = None

@app.route('/health', methods=['GET'])
def health():
    if IMPORT_ERROR:
        # Mostrar el error exacto en el navegador
        return f"ERROR AL IMPORTAR AGENTE:\n\n{IMPORT_ERROR}", 500
    return 'Max IA OK', 200

@app.route('/chat', methods=['POST'])
def chat():
    if IMPORT_ERROR:
        return jsonify({'error': f'Error de importacion: {IMPORT_ERROR}'}), 500
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400
    mensaje = data.get('message', '').strip()
    numero  = data.get('phone', 'web-visitor').strip()
    if not mensaje:
        return jsonify({'error': 'Mensaje vacio'}), 400
    respuesta = procesar_mensaje(numero, mensaje)
    return jsonify({'reply': respuesta})

if __name__ == '__main__':
    app.run(debug=True, port=5001)

