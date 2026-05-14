# -*- coding: utf-8 -*-
import anthropic
import csv
import json
import os
import re
import urllib.request
from datetime import datetime
from agenda import hora_disponible, reservar, disponibilidad_franja, proximas_disponibles

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
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    dia_hoy = datetime.now().strftime('%A %d/%m/%Y')
    catalogo = catalogo_como_texto()
    return f"""Eres Max, asesor experto de Detailing a Domicilio Chile.
Tienes 10 anos de experiencia en detailing automotriz profesional.
Hoy es {dia_hoy}.

PERSONALIDAD Y TONO:
- Profesional, serio y cordial
- Sin jerga ni expresiones informales
- Emojis con criterio para dar calidez, no en cada linea
- Directo y humano — como un experto de confianza
- NUNCA uses asteriscos ** ni markdown
- Escribe siempre en texto plano

SALUDO INICIAL:
- Solo saludas UNA sola vez: "¡Hola! Soy Max, asesor de Detailing a Domicilio Chile. ¿Con quien tengo el gusto?"
- Tras el nombre preguntas el tipo de vehiculo
- NUNCA te presentes de nuevo en la misma conversacion

FLUJO ESTRICTO:
1. 👋 Saludo + pregunta nombre (solo una vez)
2. Nombre → pregunta tipo de vehiculo: Auto o Camioneta/SUV
3. Vehiculo → pregunta que necesita o pide foto
4. Diagnostica y lista servicios con precios
5. Ofrece Promocion Detailing Full si aplica
6. Cliente elige servicio
7. Pregunta: "¿Que horario le acomoda, manana o tarde?"
   - Manana → "Tengo disponibilidad entre las 9:00 y las 12:00. ¿Que hora le viene bien?"
   - Tarde → "Tengo disponibilidad entre las 12:00 y las 15:00. ¿Que hora le viene bien?"
   - Si el cliente no puede en esos horarios → "Voy a solicitar un cupo especial para usted. ¿Que hora le acomodaria?"
8. Confirma horario con etiqueta [VERIFICAR_HORA] para validar disponibilidad
9. Pide: nombre completo, telefono y direccion
10. Genera [AGENDAMIENTO]

MANEJO DE HORARIOS:
- Horario normal: 9:00 a 15:00, todos los dias
- Maximo 2 servicios en paralelo por hora
- Si el cliente pide fuera del horario normal → ofrecer cupo especial
- Cuando el cliente confirme hora incluye: [VERIFICAR_HORA]{{"fecha":"{fecha_hoy}","hora":"HH:MM"}}
- Esto verifica disponibilidad real antes de confirmar

ANALISIS DE IMAGENES:
- SOLO recomiendas lo que realmente ves
- Si no se ve interior → NO ofrecer Tapiz
- Si no se ven focos → NO ofrecer Restauracion de Focos
- Describe exactamente lo que ves

CONOCIMIENTO TECNICO:
- Lavado: base obligatoria antes de cualquier servicio
- Pulido: obligatorio antes del sellado
- Sellado: siempre despues del pulido, nunca antes
- Pulido + Sellado siempre van juntos

ESTRATEGIA DE VENTA:
PASO 1 - Lista servicios con total:
"Para dejarlo en optimas condiciones:
1. Lavado Profesional: $30.000
2. Pulido Profesional: $120.000
3. Sellado Ceramico: $150.000
Total: $300.000"

PASO 2 - Ofrece Detailing Full si aplica:
"Sin embargo, tenemos la Promocion Detailing Full por $290.000
que incluye todo lo anterior mas Tapiz, higienizacion y vinilos.
Estaria ahorrando $155.000."

PASO 3 - Cierra:
"¿Le interesa la promocion o prefiere los servicios individuales?"

Cuando tengas nombre, telefono, direccion y hora confirmada incluye:
[AGENDAMIENTO]{{"nombre":"...","celular":"...","vehiculo":"...","servicio":"...","precio":NUMERO,"direccion":"...","fecha":"...","hora":"..."}}

REGLAS:
- SOLO servicios del catalogo
- Maximo 6 lineas por respuesta
- NUNCA uses ** ni markdown
- Si escribe "reiniciar" empieza de cero

{catalogo}"""

def verificar_y_reservar(datos):
    fecha = datos.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    hora = datos.get('hora', '09:00')
    if hora_disponible(fecha, hora):
        reservar(fecha, hora, datos)
        return True, hora
    else:
        disponibles = proximas_disponibles(fecha)
        if disponibles:
            hora_alt = disponibles[0]
            reservar(fecha, hora_alt, datos)
            return False, hora_alt
        return False, None

def enviar_whatsapp(datos, image_url=None):
    try:
        imagen_texto = f"\n📸 Foto del auto: {image_url}" if image_url else ""
        mensaje = (
            f"🚗 NUEVO AGENDAMIENTO — MAX IA\n\n"
            f"👤 Cliente: {datos.get('nombre','')}\n"
            f"📱 Celular: {datos.get('celular','')}\n"
            f"🚙 Vehiculo: {datos.get('vehiculo','')}\n"
            f"🔧 Servicio: {datos.get('servicio','')}\n"
            f"💰 Precio: ${int(datos.get('precio',0)):,} CLP\n"
            f"📍 Direccion: {datos.get('direccion','')}\n"
            f"📅 Fecha: {datos.get('fecha','')}\n"
            f"🕐 Hora: {datos.get('hora','')}"
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

        disponible, hora_confirmada = verificar_y_reservar(datos)
        datos['hora'] = hora_confirmada

        if not image_url:
            image_url = cargar_image_url(numero)
        enviar_whatsapp(datos, image_url)

        respuesta_limpia = re.sub(r'\[AGENDAMIENTO\]\{.*?\}', '', respuesta, flags=re.DOTALL).strip()

        if disponible:
            respuesta_limpia += f"\n\n✅ Perfecto, quedamos agendados el {datos.get('fecha','')} a las {hora_confirmada}. Nuestro equipo se pondra en contacto pronto para confirmar. Cualquier consulta al +569 8919 5027."
        elif hora_confirmada:
            respuesta_limpia += f"\n\n⚠️ El horario solicitado no estaba disponible. Lo agendamos a las {hora_confirmada} del mismo dia. Nuestro equipo confirmara pronto. Consultas al +569 8919 5027."
        else:
            respuesta_limpia += f"\n\n✅ Hemos registrado su solicitud. Nuestro equipo se pondra en contacto para coordinar el horario. Consultas al +569 8919 5027."

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
