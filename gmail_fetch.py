# gmail_fetch.py

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import zipfile
import io


def obtener_adjuntos(service):

    results = service.users().messages().list(
        userId="me",
        q="filename:xml OR filename:zip"
    ).execute()

    mensajes = results.get("messages", [])

    archivos = []

    for m in mensajes:

        msg = service.users().messages().get(
            userId="me",
            id=m["id"]
        ).execute()

        for part in msg["payload"].get("parts", []):

            filename = part.get("filename")

            if filename.endswith(".xml") or filename.endswith(".zip"):

                data = part["body"]["data"]
                file_bytes = base64.urlsafe_b64decode(data)

                archivos.append((filename, file_bytes))

    return archivos
