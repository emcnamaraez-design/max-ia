from flask import Flask, request, jsonify
from flask_cors import CORS
from agente_vendedor import procesar_mensaje

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return 'Max IA OK', 200

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    image_data = data.get('image', None)
    image_type = data.get('image_type', 'image/jpeg')

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

    respuesta = procesar_mensaje(numero, mensaje, image_data, image_type)
    return jsonify({'reply': respuesta})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
