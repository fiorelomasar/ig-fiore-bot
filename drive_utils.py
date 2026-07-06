Claro, es este completo:
python"""
Funciones para listar, descargar, subir y mover archivos en Google Drive
usando OAuth como el usuario real (no cuenta de servicio).

Por qué OAuth y no cuenta de servicio: las cuentas de servicio NO tienen cuota
de almacenamiento propia en Drive. En una cuenta de Gmail personal (sin Google
Workspace / unidades compartidas), cualquier intento de la cuenta de servicio de
CREAR un archivo nuevo falla con "Service Accounts do not have storage quota".
Autenticando como el usuario real, los archivos se crean con tu propia cuota.
"""

import io
import os

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _load_credentials():
    """
    Carga credenciales OAuth de usuario a partir de client_id, client_secret y
    refresh_token guardados como variables de entorno (secretos de GitHub).
    """
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        raise RuntimeError(
            "Faltan variables de entorno GOOGLE_OAUTH_CLIENT_ID, "
            "GOOGLE_OAUTH_CLIENT_SECRET y/o GOOGLE_OAUTH_REFRESH_TOKEN."
        )

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )


def get_drive_service():
    creds = _load_credentials()
    return build("drive", "v3", credentials=creds)


def list_files(service, folder_id, valid_extensions=None):
    """Devuelve lista de dicts {id, name, createdTime} de archivos en una carpeta (no incluye subcarpetas)."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = []
    page_token = None
    while True:
        response = service.files().list(
            q=query,
            spaces="drive",
            fields="nextPageToken, files(id, name, mimeType, createdTime)",
            pageToken=page_token,
        ).execute()
        for f in response.get("files", []):
            if f["mimeType"] == "application/vnd.google-apps.folder":
                continue
            if valid_extensions and not f["name"].lower().endswith(valid_extensions):
                continue
            results.append({"id": f["id"], "name": f["name"], "createdTime": f["createdTime"]})
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return results


def download_file(service, file_id):
    """Descarga el contenido de un archivo y lo devuelve como bytes."""
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    return buffer.read()


def upload_file(service, folder_id, filename, content_bytes, mime_type="image/jpeg"):
    """Sube bytes como un archivo nuevo dentro de folder_id. Devuelve el id del archivo creado."""
    file_metadata = {"name": filename, "parents": [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(content_bytes), mimetype=mime_type, resumable=False)
    created = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return created["id"]


def move_file(service, file_id, new_folder_id):
    """Mueve un archivo existente a otra carpeta (quita el parent viejo, agrega el nuevo)."""
    file = service.files().get(fileId=file_id, fields="parents").execute()
    previous_parents = ",".join(file.get("parents", []))
    service.files().update(
        fileId=file_id,
        addParents=new_folder_id,
        removeParents=previous_parents,
        fields="id, parents",
    ).execute()


def file_exists_by_name(service, folder_id, filename):
    """Chequea si ya existe un archivo con ese nombre en la carpeta dada."""
    safe_name = filename.replace("'", "\\'")
    query = f"'{folder_id}' in parents and trashed = false and name = '{safe_name}'"
    response = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
    return len(response.get("files", [])) > 0
