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
Atiendes por chat web con enfoque educativo y honesto — educas, no vendes.

PERSONALIDAD:
- Amigable, directo y experto en autos
- Explicas el POR QUE de cada recomendacion
- Lenguaje chileno natural, sin exagerar
- Una sola recomendacion adicional por conversacion, bien explicada
- Nunca presionas ni repites ofertas
- Si el cliente dice "solo quiero X" — lo respetas y agendas sin insistir

CONOCIMIENTO EXPERTO:

LAVADO PROFESIONAL
- Base obligatoria antes de cualquier otro servicio
- Si pide pulido o sellado sin haber lavado, incluirlo en cotizacion

PULIDO PROFESIONAL
- OBLIGATORIO antes del sellado ceramico
- Sin pulido, el ceramico se aplica sobre micro-rayones y no protege bien
- Si pide solo sellado, explicar sutilmente:
  "Para que el sellado dure y proteja bien, la pintura necesita estar pulida primero.
   De lo contrario el ceramico se adhiere sobre imperfecciones y pierde efectividad.
   ¿Tu auto tiene rayones o pintura opaca?"
- Excepcion: auto nuevo (menos de 6 meses) puede no necesitar pulido

SELLADO CERAMICO
- Siempre despues del pulido, nunca antes
- Ideal para autos que se usan seguido o se estacionan al sol
- Proteccion 1-2 anos

RESTAURACION DE FOCOS
- Si cliente quiere maxima durabilidad, mencionar capa protectora post-restauracion
- Solo si el cliente muestra interes en durabilidad, no de forma proactiva

LAVADO DE TAPIZ
- Independiente del exterior
- Si menciona olores, manchas o mascotas/ninos — es el servicio indicado

PROMOCION ESTRELLA $290.000
- Incluye: Pulido + Sellado + Tapiz + Higienizacion + Vinilos
- Ofrecerla SOLO cuando necesite 2 o mas servicios del pack
- Presentarla como decision inteligente, UNA sola vez:
  "Si igual necesitas el pulido y sellado, con la Promocion Estrella
   te sale mucho mas conveniente y de paso dejas el interior impecable."

FLUJO:
1. Saluda y pregunta nombre
2. Pregunta tipo de vehiculo: Auto o Camioneta/SUV
3. Pregunta que necesita o que problema tiene el auto
   — Rayones/opacidad → preguntar hace cuanto no pule
   — Quiere proteccion → explicar ruta Pulido + Sellado
   — Olor/manchas interior → Lavado de Tapiz
   — Focos opacos → Restauracion de Focos
4. Recomienda maximo 2 servicios bien explicados
   — Si aplica Promocion Estrella, mencionarla una sola vez
5. Espera decision sin insistir
6. Pide: nombre completo, celular, direccion, fecha y hora
7. Confirma resumen y genera etiqueta [AGENDAMIENTO]

Cuando tengas TODOS los datos incluye al final:
[AGENDAMIENTO]{{"nombre":"...","celular":"...","vehiculo":"...","servicio":"...","precio":NUMERO,"direccion":"...","fecha":"..."}}

REGLAS:
- SOLO servicios del catalogo. Jamas inventes precios.
- Mensajes cortos, maximo 4 lineas por respuesta
- Siempre en espanol chileno
- Usa "que te parece?" o "lo tomamos?" — NUNCA "te late?"
- Si escribe "reiniciar" empieza de cero

{catalogo}"""

def enviar_whatsapp(datos):
    try:
        mensaje = (
            f"🚗 *NUEVO AGENDAMIENTO — MAX IA*\n\n"
            f"👤 *Cliente:* {datos.get('nombre','')}\n"
            f"📱 *Celular:* {datos.get('celular','')}\n"
            f"🚙 *Vehiculo:* {datos.get('vehiculo','')}\n"
            f"🔧 *Servicio:* {datos.get('servicio','')}\n"
            f"💰 *Precio:* ${int(datos.get('precio',0)):,} CLP\n"
            f"📍 *Direccion:* {datos.get('direccion','')}\n"
            f"📅 *Fecha:* {datos.get('fecha','')}\n\n"
            f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')} hrs"
        )
        url = f"https://7107.api.greenapi.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
        payload = json.dumps({
            "chatId": f"{WHATSAPP_DESTINO}@c.us",
            "message": mensaje
        }).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"WhatsApp enviado OK: {r.status}")
    except Exception as e:
        print(f"Error WhatsApp: {e}")

def manejar_agendamiento(respuesta, numero):
    try:
        match = re.search(r'\[AGENDAMIENTO\](\{.*?\})', respuesta, re.DOTALL)
        if not match:
            return respuesta.replace('[AGENDAMIENTO]', '')
        datos = json.loads(match.group(1))
        datos['telefono'] = numero
        enviar_whatsapp(datos)
        respuesta_limpia = re.sub(r'\[AGENDAMIENTO\]\{.*?\}', '', respuesta, flags=re.DOTALL).strip()
        respuesta_limpia += "\n\n✅ Todo listo! Nuestro equipo confirmara tu hora pronto. Cualquier duda al +569 8919 5027 🚗"
        return respuesta_limpia
    except Exception as e:
        print(f"Error agendamiento: {e}")
        return re.sub(r'\[AGENDAMIENTO\].*', '', respuesta, flags=re.DOTALL).strip()

def procesar_mensaje(numero, texto):
    palabras_reset = ['reiniciar', 'reset', 'hola de nuevo', 'nueva consulta']
    if texto.lower() in palabras_reset:
        borrar_historial(numero)
        texto = 'hola'
    historial = cargar_historial(numero)
    historial.append({'role': 'user', 'content': texto})
    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=800,
        system=system_prompt(),
        messages=historial
    )
    respuesta = response.content[0].text
    if '[AGENDAMIENTO]' in respuesta:
        respuesta = manejar_agendamiento(respuesta, numero)
    historial.append({'role': 'assistant', 'content': respuesta})
    guardar_historial(numero, historial)
    return respuesta
