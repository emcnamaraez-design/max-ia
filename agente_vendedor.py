# -*- coding: utf-8 -*-
import anthropic
import csv
import json
import os
import re
import urllib.request
from datetime import datetime

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
CARPETA_HISTORIAL = os.path.join(os.path.dirname(__file__), 'historial')
os.makedirs(CARPETA_HISTORIAL, exist_ok=True)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

GREEN_API_INSTANCE = '7107619976'
GREEN_API_TOKEN = 'e2617c1799fa4734ad9bc83e0810cdd7e435ae7e865b455f8f'
WHATSAPP_DESTINO = '56989195027'

def cargar_servicios():
    servicios = []
    ruta = os.path.join(os.path.dirname(__file__), 'servicios.csv')
    with open(ruta, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for fila in reader:
            servicios.append(fila)
    return servicios

def catalogo_como_texto():
    servicios = cargar_servicios()
    texto = "=== SERVICIOS DISPONIBLES ===\n\n"
    for s in servicios:
        texto += f"{s['emoji']} {s['nombre'].upper()}\n"
        texto += f"   Precio Auto: ${int(s['precio_auto']):,}\n"
        if s['precio_auto'] != s['precio_camioneta']:
            texto += f"   Precio Camioneta/SUV: ${int(s['precio_camioneta']):,}\n"
        texto += f"   Duracion: {s['duracion_min']} minutos\n\n"
    texto += "\n🌟 PROMOCION DETAILING FULL: $290.000\n"
    texto += "   Incluye: Pulido Profesional + Sellado Ceramico + Lavado de Tapiz + Higienizacion + Vinilos\n"
    texto += "   (Valor normal por separado: $445.000 — ahorro de $155.000)\n"
    return texto

def cargar_historial(numero):
    archivo = os.path.join(CARPETA_HISTORIAL, f"{numero}.json")
    if os.path.exists(archivo):
        with open(archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def guardar_historial(numero, mensajes):
    archivo = os.path.join(CARPETA_HISTORIAL, f"{numero}.json")
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(mensajes, f, ensure_ascii=False, indent=2)

def borrar_historial(numero):
    archivo = os.path.join(CARPETA_HISTORIAL, f"{numero}.json")
    if os.path.exists(archivo):
        os.remove(archivo)

def cargar_image_url(numero):
    archivo = os.path.join(CARPETA_HISTORIAL, f"{numero}_img.txt")
    if os.path.exists(archivo):
        with open(archivo, 'r') as f:
            return f.read().strip()
    return None

def guardar_image_url(numero, url):
    archivo = os.path.join(CARPETA_HISTORIAL, f"{numero}_img.txt")
    with open(archivo, 'w') as f:
        f.write(url)

def system_prompt():
    catalogo = catalogo_como_texto()
    return f"""Eres Max, asesor experto de Detailing a Domicilio Chile.
Tienes 10 anos de experiencia en detailing automotriz profesional.
Tu objetivo es asesorar con honestidad y cerrar ventas de forma natural.

PERSONALIDAD Y TONO:
- Profesional, serio y cordial
- Sin jerga, sin "po", sin expresiones informales
- Emojis solo cuando aporten claridad, no en cada linea
- Directo y humano — como un experto de confianza
- NUNCA uses asteriscos ** ni markdown de ningun tipo
- Escribe siempre en texto plano

SALUDO INICIAL — MUY IMPORTANTE:
- Solo saludas UNA sola vez al inicio de la conversacion
- El saludo es UNICAMENTE: "Hola, soy Max, asesor de Detailing a Domicilio Chile. ¿Con quien tengo el gusto?"
- Despues de que el cliente da su nombre, preguntas el tipo de vehiculo
- NUNCA repitas el saludo ni te presentes de nuevo en la misma conversacion

FLUJO ESTRICTO:
1. Saludo + pregunta nombre (solo una vez)
2. Cliente da nombre → preguntas tipo de vehiculo: Auto o Camioneta/SUV
3. Cliente da vehiculo → preguntas que necesita o que problema tiene
   Si envia imagen → analizas y diagnosticas (ver reglas de imagen)
4. Listas servicios necesarios con precios
5. Ofreces Promocion Detailing Full si aplica
6. Esperas decision
7. Pides datos: nombre completo, celular, direccion, fecha y hora
8. Confirmas y generas [AGENDAMIENTO]

ANALISIS DE IMAGENES — COHERENCIA OBLIGATORIA:
- SOLO recomiendas lo que realmente ves en la imagen
- Si no se ve el interior → NO ofrecer Lavado de Tapiz
- Si no se ven los focos → NO ofrecer Restauracion de Focos
- Si ves rayones o pintura opaca → recomendar Lavado + Pulido + Sellado
- Si ves interior sucio o manchas → recomendar Lavado de Tapiz
- Si ves focos opacos → recomendar Restauracion de Focos
- Describe exactamente lo que ves: "En la imagen veo rayones en la puerta y pintura con perdida de brillo en el capo."
- No asumas lo que no ves

CONOCIMIENTO TECNICO:

LAVADO PROFESIONAL
- Base obligatoria antes de cualquier otro servicio

PULIDO PROFESIONAL
- Elimina rayones superficiales y restaura el brillo
- Paso previo obligatorio al sellado ceramico
- Sin pulido, el ceramico pierde efectividad

SELLADO CERAMICO
- Protege la pintura 1 a 2 anos
- Solo se aplica despues del pulido, jamas antes
- Pulido y sellado siempre van juntos

RESTAURACION DE FOCOS
- Elimina opacidad y amarillamiento
- Solo ofrecer si se ven opacos o el cliente lo menciona

LAVADO DE TAPIZ
- Solo ofrecer si se ve el interior sucio o el cliente lo menciona

PROMOCION DETAILING FULL $290.000
- Incluye: Pulido + Sellado Ceramico + Lavado de Tapiz + Higienizacion + Vinilos
- Valor por separado: $445.000 — ahorro real de $155.000
- Ofrecer cuando aplican 2 o mas servicios del pack

ESTRATEGIA DE VENTA:

PASO 1 — Lista servicios necesarios con total:
"Para dejarlo en optimas condiciones necesitaria:
1. Lavado Profesional: $30.000
2. Pulido Profesional: $120.000
3. Sellado Ceramico: $150.000
Total: $300.000"

PASO 2 — Ofrece la Promocion si aplica:
"Sin embargo, tenemos disponible nuestra Promocion Detailing Full por $290.000
que incluye todo lo anterior mas Lavado de Tapiz, higienizacion y vinilos.
Estaria ahorrando $155.000 con respecto a contratar cada servicio por separado."

PASO 3 — Cierra:
"Le interesa la promocion o prefiere los servicios individuales?"

Cuando tengas TODOS los datos incluye al final:
[AGENDAMIENTO]{{"nombre":"...","celular":"...","vehiculo":"...","servicio":"...","precio":NUMERO,"direccion":"...","fecha":"..."}}

REGLAS:
- SOLO servicios del catalogo. Jamas inventes precios.
- Maximo 6 lineas por respuesta
- Siempre en espanol formal pero cercano
- NUNCA uses ** ni markdown
- Si escribe "reiniciar" empieza de cero

{catalogo}"""

def enviar_whatsapp(datos, image_url=None):
    try:
        imagen_texto = f"\n📸 Foto del auto: {image_url}" if image_url else ""
        mensaje = (
            f"🚗 NUEVO AGENDAMIENTO — MAX IA\n\n"
            f"Cliente: {datos.get('nombre','')}\n"
            f"Celular: {datos.get('celular','')}\n"
            f"Vehiculo: {datos.get('vehiculo','')}\n"
            f"Servicio: {datos.get('servicio','')}\n"
            f"Precio: ${int(datos.get('precio',0)):,} CLP\n"
            f"Direccion: {datos.get('direccion','')}\n"
            f"Fecha: {datos.get('fecha','')}"
            f"{imagen_texto}"
        )
        url = f"https://7107.api.greenapi.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
        payload = json.dumps({
            "chatId": f"{WHATSAPP_DESTINO}@c.us",
            "message": mensaje
        }).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"WhatsApp OK: {r.status}")
    except Exception as e:
        print(f"Error WhatsApp: {e}")

def manejar_agendamiento(respuesta, numero, image_url=None):
    try:
        match = re.search(r'\[AGENDAMIENTO\](\{.*?\})', respuesta, re.DOTALL)
        if not match:
            return respuesta.replace('[AGENDAMIENTO]', '')
        datos = json.loads(match.group(1))
        datos['telefono'] = numero
        if not image_url:
            image_url = cargar_image_url(numero)
        enviar_whatsapp(datos, image_url)
        respuesta_limpia = re.sub(r'\[AGENDAMIENTO\]\{.*?\}', '', respuesta, flags=re.DOTALL).strip()
        respuesta_limpia += "\n\nPerfecto. Hemos registrado su solicitud y nuestro equipo se pondra en contacto pronto para confirmar. Cualquier consulta puede escribirnos al +569 8919 5027."
        return respuesta_limpia
    except Exception as e:
        print(f"Error agendamiento: {e}")
        return re.sub(r'\[AGENDAMIENTO\].*', '', respuesta, flags=re.DOTALL).strip()

def procesar_mensaje(numero, texto, image_data=None, image_type='image/jpeg', image_url=None):
    palabras_reset = ['reiniciar', 'reset', 'hola de nuevo', 'nueva consulta']
    if texto.lower() in palabras_reset:
        borrar_historial(numero)
        texto = 'hola'

    historial = cargar_historial(numero)

    if image_url:
        guardar_image_url(numero, image_url)

    if image_data:
        if not texto or texto == 'hola':
            texto = 'Analiza esta foto de mi auto y dime que servicios necesita.'
        mensaje_claude = {
            'role': 'user',
            'content': [
                {
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': image_type,
                        'data': image_data
                    }
                },
                {'type': 'text', 'text': texto}
            ]
        }
        historial_guardado = historial + [{'role': 'user', 'content': f'[imagen enviada] {texto}'}]
    else:
        mensaje_claude = {'role': 'user', 'content': texto}
        historial_guardado = historial + [{'role': 'user', 'content': texto}]

    mensajes_api = historial + [mensaje_claude]

    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=800,
        system=system_prompt(),
        messages=mensajes_api
    )
    respuesta = response.content[0].text

    if '[AGENDAMIENTO]' in respuesta:
        respuesta = manejar_agendamiento(respuesta, numero, image_url)

    historial_guardado.append({'role': 'assistant', 'content': respuesta})
    guardar_historial(numero, historial_guardado)
    return respuesta
