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
    if 'message' in data:
        mensaje = data.get('message', '').strip()
        numero  = data.get('phone', 'web-visitor').strip()
    elif 'messages' in data:
        mensajes = data.get('messages', [])
        mensaje = ''
        for m in reversed(mensajes):
            if m.get('role') == 'user' and m.get('content') != 'INICIO':
                mensaje = m.get('content', '').strip()
                break
        if not mensaje or mensaje == 'INICIO':
            mensaje = 'hola'
        numero = 'web-visitor'
    else:
        return jsonify({'error': 'Formato incorrecto'}), 400
    if not mensaje:
        return jsonify({'error': 'Mensaje vacio'}), 400
    respuesta = procesar_mensaje(numero, mensaje)
    return jsonify({'reply': respuesta})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
