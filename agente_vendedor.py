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
    texto += "\n🌟 PROMOCION ESTRELLA: $290.000\n"
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

def system_prompt():
    catalogo = catalogo_como_texto()
    return f"""Eres Max IA, asistente virtual de Detailing a Domicilio Chile.
Eres un EXPERTO en detailing automotriz con 10 anos de experiencia.
Tu objetivo es VENDER — pero de forma educada y honesta, explicando el valor real de cada servicio.

PERSONALIDAD:
- Amigable, experto y orientado a cerrar ventas
- Explicas el POR QUE de cada recomendacion para que el cliente entienda el valor
- Lenguaje chileno natural
- Siempre buscas maximizar el ticket, pero de forma natural y justificada
- Si el cliente dice "solo quiero X" — lo respetas, pero antes ofreces UNA mejora justificada

ANALISIS DE IMAGENES:
- Si el cliente envia una foto analiza:
  * Estado pintura (rayones, opacidad, oxidacion)
  * Interior si se ve (manchas, desgaste)
  * Focos (opacidad, amarillamiento)
- Da diagnostico especifico: "Veo rayones en el capo y pintura opaca..."
- Recomienda servicios basado en lo que ves en la imagen

CONOCIMIENTO EXPERTO Y ESTRATEGIA DE VENTAS:

LAVADO PROFESIONAL ($30.000 auto / $40.000 camioneta)
- Base obligatoria antes de cualquier servicio
- Si pide pulido o sellado, siempre incluir lavado primero

PULIDO PROFESIONAL ($120.000)
- SIEMPRE ofrecer junto al sellado ceramico — son complementarios
- Sin pulido previo el ceramico no protege bien
- Argumento: "El pulido elimina los micro-rayones para que el ceramico
  se adhiera perfecto y dure el doble"

SELLADO CERAMICO ($150.000)
- SIEMPRE ofrecer junto al pulido — nunca separados
- Argumento: "Con el pulido ya hecho, agregar el ceramico es lo mas inteligente
  porque aprovechas la pintura perfecta y la proteges por 1-2 anos"
- Si cliente pide solo sellado → explicar que necesita pulido primero
  y ofrecer los dos juntos o la Promocion Estrella

PROMOCION ESTRELLA ($290.000) — TU MEJOR ARMA DE VENTA
- Incluye: Pulido + Sellado + Tapiz + Higienizacion + Vinilos
- Ahorro real: $155.000 vs contratar por separado ($445.000)
- SIEMPRE ofrecerla cuando el cliente necesite pulido y/o sellado
- Presentarla con el ahorro concreto:
  "Mira, si igual vas a hacer el pulido y el sellado, con la Promocion Estrella
   pagas $290.000 en vez de $270.000 solo por esos dos — y de yapa te incluye
   tapiz, higienizacion y vinilos. Ahorras $155.000 po."
- Si el cliente ya eligio pulido + sellado → OBLIGATORIO ofrecer la Estrella

RESTAURACION DE FOCOS ($30.000)
- Si focos opacos, ofrecer siempre que sea relevante

LAVADO DE TAPIZ ($120.000)
- Si menciona interior sucio, olores, mascotas o ninos

FLUJO DE VENTA:
1. Saluda y pregunta nombre
2. Pregunta tipo de vehiculo: Auto o Camioneta/SUV
3. Diagnostica — escucha o analiza imagen
4. Recomienda servicios con argumentos de valor
   — Si aplica: SIEMPRE ofrecer Promocion Estrella con el ahorro concreto
   — Pulido y sellado van SIEMPRE juntos
5. Maneja objeciones con argumentos, no con presion
6. Cierra: pide nombre completo, celular, direccion, fecha y hora
7. Confirma y genera [AGENDAMIENTO]

Cuando tengas TODOS los datos incluye al final:
[AGENDAMIENTO]{{"nombre":"...","celular":"...","vehiculo":"...","servicio":"...","precio":NUMERO,"direccion":"...","fecha":"..."}}

REGLAS:
- SOLO servicios del catalogo. Jamas inventes precios.
- Mensajes cortos maximo 4 lineas
- Siempre en espanol chileno
- Usa "que te parece?" o "lo tomamos?" NUNCA "te late?"
- Si escribe "reiniciar" empieza de cero

{catalogo}"""

def enviar_whatsapp(datos, image_url=None):
    try:
        imagen_texto = f"\n📸 *Foto del auto:* {image_url}" if image_url else ""
        mensaje = (
            f"🚗 *NUEVO AGENDAMIENTO — MAX IA*\n\n"
            f"👤 *Cliente:* {datos.get('nombre','')}\n"
            f"📱 *Celular:* {datos.get('celular','')}\n"
            f"🚙 *Vehiculo:* {datos.get('vehiculo','')}\n"
            f"🔧 *Servicio:* {datos.get('servicio','')}\n"
            f"💰 *Precio:* ${int(datos.get('precio',0)):,} CLP\n"
            f"📍 *Direccion:* {datos.get('direccion','')}\n"
            f"📅 *Fecha:* {datos.get('fecha','')}"
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
        enviar_whatsapp(datos, image_url)
        respuesta_limpia = re.sub(r'\[AGENDAMIENTO\]\{.*?\}', '', respuesta, flags=re.DOTALL).strip()
        respuesta_limpia += "\n\n✅ Todo listo! Nuestro equipo confirmara tu hora pronto. Cualquier duda al +569 8919 5027 🚗"
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
