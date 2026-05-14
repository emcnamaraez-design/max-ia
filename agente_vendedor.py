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

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

GMAIL_USER = 'emcnamaraez@gmail.com'
GMAIL_PASS = 'gbpswkaogzumzdcy'
EMAIL_DESTINO = 'emcnamaraez@gmail.com'

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
- Siempre en espanol chileno

{catalogo}"""

def enviar_email_admin(datos):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_USER
        msg['To'] = EMAIL_DESTINO
        msg['Subject'] = f"🚗 Nuevo Agendamiento - {datos.get('nombre','')} - {datos.get('servicio','')}"

        html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:30px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">

        <!-- HEADER -->
        <tr>
          <td style="background:linear-gradient(135deg,#0d1b2a 60%,#1a3a5c);padding:30px;text-align:center;">
            <div style="font-size:32px;margin-bottom:8px;">🚗</div>
            <h1 style="color:white;margin:0;font-size:22px;font-weight:700;letter-spacing:1px;">DETAILING A DOMICILIO</h1>
            <p style="color:rgba(255,255,255,0.7);margin:5px 0 0;font-size:13px;">www.detailingadomicilio.cl</p>
          </td>
        </tr>

        <!-- BADGE -->
        <tr>
          <td style="padding:25px 30px 10px;text-align:center;">
            <span style="background:#e8f4fd;color:#1565c0;padding:8px 20px;border-radius:20px;font-size:13px;font-weight:600;">✅ NUEVO AGENDAMIENTO RECIBIDO</span>
            <p style="color:#666;font-size:12px;margin:10px 0 0;">{datetime.now().strftime('%d/%m/%Y a las %H:%M')} hrs</p>
          </td>
        </tr>

        <!-- DATOS CLIENTE -->
        <tr>
          <td style="padding:15px 30px;">
            <h2 style="color:#0d1b2a;font-size:15px;margin:0 0 15px;border-bottom:2px solid #f0f4f8;padding-bottom:8px;">👤 DATOS DEL CLIENTE</h2>
            <table width="100%" cellpadding="8" cellspacing="0">
              <tr style="background:#f8fafc;">
                <td style="color:#666;font-size:13px;width:35%;border-radius:6px 0 0 6px;padding:10px 12px;"><strong>Nombre</strong></td>
                <td style="color:#0d1b2a;font-size:13px;font-weight:600;border-radius:0 6px 6px 0;padding:10px 12px;">{datos.get('nombre','')}</td>
              </tr>
              <tr>
                <td style="color:#666;font-size:13px;padding:10px 12px;"><strong>Celular</strong></td>
                <td style="color:#0d1b2a;font-size:13px;padding:10px 12px;">{datos.get('celular','')}</td>
              </tr>
              <tr style="background:#f8fafc;">
                <td style="color:#666;font-size:13px;padding:10px 12px;border-radius:6px 0 0 6px;"><strong>Vehiculo</strong></td>
                <td style="color:#0d1b2a;font-size:13px;padding:10px 12px;border-radius:0 6px 6px 0;">{datos.get('vehiculo','')}</td>
              </tr>
              <tr>
                <td style="color:#666;font-size:13px;padding:10px 12px;"><strong>Direccion</strong></td>
                <td style="color:#0d1b2a;font-size:13px;padding:10px 12px;">{datos.get('direccion','')}</td>
              </tr>
              <tr style="background:#f8fafc;">
                <td style="color:#666;font-size:13px;padding:10px 12px;border-radius:6px 0 0 6px;"><strong>Fecha</strong></td>
                <td style="color:#0d1b2a;font-size:13px;padding:10px 12px;border-radius:0 6px 6px 0;">{datos.get('fecha','')}</td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- SERVICIO -->
        <tr>
          <td style="padding:10px 30px 25px;">
            <h2 style="color:#0d1b2a;font-size:15px;margin:0 0 15px;border-bottom:2px solid #f0f4f8;padding-bottom:8px;">🔧 SERVICIO SOLICITADO</h2>
            <table width="100%" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#0d1b2a,#1a3a5c);border-radius:10px;overflow:hidden;">
              <tr>
                <td style="padding:20px;color:white;">
                  <p style="margin:0;font-size:16px;font-weight:700;">{datos.get('servicio','')}</p>
                  <p style="margin:5px 0 0;font-size:13px;color:rgba(255,255,255,0.7);">{datos.get('vehiculo','')}</p>
                </td>
                <td style="padding:20px;text-align:right;">
                  <p style="margin:0;font-size:22px;font-weight:800;color:white;">${int(datos.get('precio',0)):,}</p>
                  <p style="margin:3px 0 0;font-size:11px;color:rgba(255,255,255,0.6);">CLP</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="background:#f8fafc;padding:20px 30px;text-align:center;border-top:1px solid #eee;">
            <p style="color:#999;font-size:12px;margin:0;">Este mensaje fue generado automáticamente por <strong>Max IA</strong></p>
            <p style="color:#999;font-size:12px;margin:5px 0 0;">📞 +569 8919 5027 | 🌐 detailingadomicilio.cl</p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as srv:
            srv.login(GMAIL_USER, GMAIL_PASS)
            srv.sendmail(GMAIL_USER, EMAIL_DESTINO, msg.as_string())
        print("Email enviado OK")
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
