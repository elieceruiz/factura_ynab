# gmail_fetch.py

# ---------------------------------------
# IMPORTS
# ---------------------------------------

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import base64
import zipfile
import io


# ---------------------------------------
# PERMISOS GMAIL
# ---------------------------------------

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


# ---------------------------------------
# CONECTAR CON GMAIL
# ---------------------------------------

def conectar_gmail():
    """
    Abre conexión con Gmail usando OAuth2.
    """

    creds = None

    if os.path.exists("token.json"):
        with open("token.json", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0, open_browser=False)

        with open("token.json", "wb") as token:
            pickle.dump(creds, token)

    service = build("gmail", "v1", credentials=creds)

    return service


# ---------------------------------------
# FUNCIÓN RECURSIVA PARA BUSCAR ADJUNTOS
# ---------------------------------------

def _recorrer_partes(parts, msg_id, service, archivos):

    for part in parts:

        filename = part.get("filename")

        if filename:

            filename = filename.lower()

            if filename.endswith(".xml") or filename.endswith(".zip"):

                body = part.get("body", {})

                if "data" in body:

                    data = body["data"]

                else:

                    att_id = body.get("attachmentId")

                    if not att_id:
                        continue

                    att = service.users().messages().attachments().get(
                        userId="me",
                        messageId=msg_id,
                        id=att_id
                    ).execute()

                    data = att["data"]

                file_bytes = base64.urlsafe_b64decode(data)

                archivos.append({
                    "filename": filename,
                    "data": file_bytes
                })

        # 👇 CLAVE: buscar adjuntos en niveles internos (correos reenviados)
        if "parts" in part:
            _recorrer_partes(part["parts"], msg_id, service, archivos)


# ---------------------------------------
# BUSCAR CORREOS CON FACTURAS
# ---------------------------------------

def obtener_adjuntos(service, dias):

    """
    Busca correos con adjuntos y devuelve
    archivos XML o ZIP encontrados.
    """

    results = service.users().messages().list(
        userId="me",
        q=f"has:attachment newer_than:{dias}d"
    ).execute()

    mensajes = results.get("messages", [])

    archivos = []

    for m in mensajes:

        msg = service.users().messages().get(
            userId="me",
            id=m["id"]
        ).execute()

        payload = msg.get("payload", {})
        parts = payload.get("parts", [])

        _recorrer_partes(parts, m["id"], service, archivos)

    return archivos


# ---------------------------------------
# EXTRAER XML SI EL ARCHIVO ES ZIP
# ---------------------------------------

def extraer_xml(archivo):

    """
    Recibe un archivo (xml o zip)
    y devuelve el XML listo para parsear.
    """

    filename = archivo["filename"]
    data = archivo["data"]

    if filename.endswith(".xml"):
        return data

    if filename.endswith(".zip"):

        try:

            with zipfile.ZipFile(io.BytesIO(data)) as z:

                for name in z.namelist():

                    if name.lower().endswith(".xml"):
                        return z.read(name)

        except zipfile.BadZipFile:
            return None

    return None