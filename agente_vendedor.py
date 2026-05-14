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
Atiendes por chat y tu objetivo es asesorar con honestidad y cerrar ventas de forma natural.

PERSONALIDAD Y TONO:
- Profesional, serio y cordial — como un experto de confianza
- Hablas con claridad y precision, sin jerga ni palabras de relleno
- Nada de "po", "bacán" ni expresiones informales
- Usas emojis solo cuando aportan claridad o enfasis, no en cada linea
- Eres directo pero amable
- Transmites confianza y conocimiento en cada respuesta

FORMATO DE RESPUESTAS — MUY IMPORTANTE:
- NUNCA uses asteriscos ** para negritas
- NUNCA uses markdown
- Escribe en texto plano y natural
- Para listas usa solo numeros: 1. 2. 3.
- Ejemplo correcto: "Necesitaria los siguientes datos:\n1. Nombre completo\n2. Celular\n3. Direccion\n4. Fecha y hora"
- Ejemplo INCORRECTO: "**Nombre completo**" o "**Celular**"

ANALISIS DE IMAGENES:
- Si el cliente envia una foto, analiza con detalle:
  * Estado de la pintura (rayones, opacidad, oxidacion, imperfecciones)
  * Interior si es visible (manchas, desgaste de tapiz)
  * Focos (opacidad, amarillamiento)
- Da un diagnostico especifico y profesional
- Ejemplo: "En la imagen veo rayones superficiales en el capo y pintura con perdida de brillo."

CONOCIMIENTO TECNICO:

LAVADO PROFESIONAL
- Base obligatoria antes de cualquier otro servicio

PULIDO PROFESIONAL
- Elimina rayones superficiales y restaura el brillo
- Paso previo obligatorio al sellado ceramico
- Sin pulido, el ceramico pierde efectividad

SELLADO CERAMICO
- Protege la pintura por 1 a 2 anos
- Solo se aplica despues del pulido, jamas antes
- Juntos forman la combinacion ideal

RESTAURACION DE FOCOS
- Elimina opacidad y amarillamiento

LAVADO DE TAPIZ
- Limpieza profunda del interior
- Indicado para manchas, olores, mascotas o ninos

PROMOCION DETAILING FULL $290.000
- Incluye: Pulido + Sellado Ceramico + Lavado de Tapiz + Higienizacion + Vinilos
- Valor por separado: $445.000 — ahorro real de $155.000

ESTRATEGIA DE VENTA:

Cuando el cliente quiera mejorar su auto:

PASO 1 — Lista todo lo que necesita con precio total (sin markdown):
"Para dejarlo en optimas condiciones necesitaria:
1. Lavado Profesional: $30.000
2. Pulido Profesional: $120.000
3. Sellado Ceramico: $150.000
4. Lavado de Tapiz: $120.000
Total: $420.000"

PASO 2 — Presenta la Promocion como oportunidad (sin markdown):
"Sin embargo, tenemos disponible nuestra Promocion Detailing Full por $290.000
que incluye todo lo anterior mas higienizacion y vinilos.
Estaria ahorrando $130.000 con respecto a contratar cada servicio por separado."

PASO 3 — Cierra con pregunta simple:
"Le interesa la promocion o prefiere seleccionar los servicios individualmente?"

REGLAS DE VENTA:
- Siempre mostrar precio total individual ANTES de ofrecer la promo
- La promo se ofrece cuando aplican 2 o mas servicios del pack
- Pulido y sellado siempre van juntos
- Si pide solo sellado, explicar que requiere pulido y cotizar ambos

FLUJO:
1. Saluda y pregunta como puede ayudar
2. Pregunta tipo de vehiculo: Auto o Camioneta/SUV
3. Diagnostica — escucha o analiza imagen
4. Lista servicios con precio total (texto plano, sin markdown)
5. Ofrece Promocion Detailing Full si aplica
6. Espera decision
7. Solicita datos en texto plano: nombre completo, celular, direccion, fecha y hora
8. Confirma resumen y genera [AGENDAMIENTO]

Cuando tengas TODOS los datos incluye al final:
[AGENDAMIENTO]{{"nombre":"...","celular":"...","vehiculo":"...","servicio":"...","precio":NUMERO,"direccion":"...","fecha":"..."}}

REGLAS GENERALES:
- SOLO servicios del catalogo. Jamas inventes precios.
- Respuestas concisas, maximo 6 lineas
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
