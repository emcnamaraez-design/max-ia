# -*- coding: utf-8 -*-
import anthropic
import csv
import json
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
CARPETA_HISTORIAL = os.path.join(os.path.dirname(__file__), 'historial')
os.makedirs(CARPETA_HISTORIAL, exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'cotizaciones'), exist_ok=True)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


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
    return f"""Eres Max IA, el asistente virtual de Detailing a Domicilio Chile.
Atiendes clientes por el chat del sitio web. Tu objetivo es entender que necesita el auto del cliente,
recomendar el servicio correcto y agendar la visita.

PERSONALIDAD:
- Amigable, eficiente y conocedor de autos
- Usas lenguaje chileno natural
- Vas al grano, sin preguntas innecesarias

FLUJO:
1. Saluda y pregunta el nombre
2. Pregunta tipo de vehiculo: Auto o Camioneta/SUV
3. Pregunta que necesita el auto
4. Recomienda 2-3 servicios. SIEMPRE menciona la Promocion Estrella $290.000
5. Cliente elige
6. Pide: nombre completo, celular, direccion, fecha y hora
7. Confirma todo y genera etiqueta [AGENDAMIENTO]

Cuando tengas todos los datos incluye al final:
[AGENDAMIENTO]{{"nombre":"...","celular":"...","vehiculo":"...","servicio":"...","precio":NUMERO,"direccion":"...","fecha":"..."}}

REGLAS:
- SOLO usa servicios del catalogo
- Si escribe "reiniciar" empieza de cero
- Mensajes cortos y directos
- Siempre en español chileno

{catalogo}"""


def enviar_email_admin(datos):
    try:
        msg = MIMEMultipart()
        msg['From'] = 'contacto@detailingadomicilio.cl'
        msg['To'] = 'emcnamaraez@gmail.com'
        msg['Subject'] = f"Nuevo Agendamiento - {datos.get('nombre','')} - {datos.get('servicio','')}"
        cuerpo = f"""
Nuevo agendamiento recibido por Max IA:

Cliente:    {datos.get('nombre', '')}
Celular:    {datos.get('celular', '')}
Vehiculo:   {datos.get('vehiculo', '')}
Servicio:   {datos.get('servicio', '')}
Precio:     ${int(datos.get('precio', 0)):,} CLP
Direccion:  {datos.get('direccion', '')}
Fecha:      {datos.get('fecha', '')}
Registrado: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """
        msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
        with smtplib.SMTP('localhost', 25) as srv:
            srv.sendmail(msg['From'], msg['To'], msg.as_string())
    except Exception as e:
        print(f"Error email: {e}")


def manejar_agendamiento(respuesta, numero):
    try:
        match = re.search(r'\[AGENDAMIENTO\](\{.*?\})', respuesta, re.DOTALL)
        if not match:
            return respuesta.replace('[AGENDAMIENTO]', '')
        datos = json.loads(match.group(1))
        datos['telefono'] = numero
        enviar_email_admin(datos)
        respuesta_limpia = re.sub(r'\[AGENDAMIENTO\]\{.*?\}', '', respuesta, flags=re.DOTALL).strip()
        respuesta_limpia += "\n\n✅ Todo listo! Nuestro equipo confirmara tu hora pronto. Cualquier duda al +569 8919 5027"
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

