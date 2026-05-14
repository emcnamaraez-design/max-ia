from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agente_vendedor import procesar_mensaje
from agenda import agenda_del_dia
import os, base64, time
from datetime import datetime

app = Flask(__name__)
CORS(app)

CARPETA_IMAGENES = os.path.join(os.path.dirname(__file__), 'cotizaciones')
os.makedirs(CARPETA_IMAGENES, exist_ok=True)

@app.route('/health', methods=['GET'])
def health():
    return 'Max IA OK', 200

@app.route('/imagen/<filename>', methods=['GET'])
def servir_imagen(filename):
    return send_from_directory(CARPETA_IMAGENES, filename)

@app.route('/agenda', methods=['GET'])
def ver_agenda():
    fecha = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    reservas = agenda_del_dia(fecha)
    if not reservas:
        return jsonify({'fecha': fecha, 'mensaje': 'Sin reservas', 'reservas': []})
    return jsonify({'fecha': fecha, 'reservas': reservas})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    image_data = data.get('image', None)
    image_type = data.get('image_type', 'image/jpeg')
    image_url = None

    if image_data:
        try:
            ext = 'jpg' if 'jpeg' in image_type else image_type.split('/')[-1]
            filename = f"img_{int(time.time())}.{ext}"
            filepath = os.path.join(CARPETA_IMAGENES, filename)
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(image_data))
            image_url = f"https://max-ia.onrender.com/imagen/{filename}"
        except Exception as e:
            print(f"Error guardando imagen: {e}")

    if 'message' in data:
        mensaje = data.get('message', '').strip()
        numero  = data.get('phone', 'web-visitor').strip()
    elif 'messages' in data:
        mensajes = data.get('messages', [])
        mensaje = ''
        for m in reversed(mensajes):
            if m.get('role') == 'user' and m.get('content') not in ['INICIO', '']:
                contenido = m.get('content', '')
                if not contenido.startswith('[imagen]'):
                    mensaje = contenido.strip()
                    break
        if data.get('text'):
            mensaje = data.get('text', '').strip()
        if not mensaje:
            mensaje = 'hola'
        numero = 'web-visitor'
    else:
        return jsonify({'error': 'Formato incorrecto'}), 400

    if not mensaje:
        mensaje = 'hola'

    respuesta = procesar_mensaje(numero, mensaje, image_data, image_type, image_url)
    return jsonify({'reply': respuesta})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
