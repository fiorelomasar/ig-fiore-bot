"""
Publicación en Instagram usando la Graph API de Meta.
Flujo: crear "media container" con la URL pública de la imagen -> publicarlo.
"""

import time
import requests

import config

GRAPH_BASE = f"https://graph.facebook.com/{config.GRAPH_API_VERSION}"


def create_media_container(image_url, caption=None):
    url = f"{GRAPH_BASE}/{config.IG_USER_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption or config.DEFAULT_CAPTION,
        "access_token": config.IG_ACCESS_TOKEN,
    }
    resp = requests.post(url, data=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["id"]


def wait_until_container_ready(container_id, max_wait_seconds=120, poll_interval=5):
    """Espera a que Instagram termine de descargar/procesar la imagen del container."""
    url = f"{GRAPH_BASE}/{container_id}"
    waited = 0
    while waited < max_wait_seconds:
        resp = requests.get(url, params={
            "fields": "status_code",
            "access_token": config.IG_ACCESS_TOKEN,
        }, timeout=30)
        resp.raise_for_status()
        status = resp.json().get("status_code")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            raise RuntimeError(f"El container {container_id} falló al procesarse.")
        time.sleep(poll_interval)
        waited += poll_interval
    raise TimeoutError(f"El container {container_id} no terminó de procesarse a tiempo.")


def publish_container(container_id):
    url = f"{GRAPH_BASE}/{config.IG_USER_ID}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": config.IG_ACCESS_TOKEN,
    }
    resp = requests.post(url, data=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["id"]


def publish_image(image_url, caption=None):
    """Orquesta el flujo completo: crear container, esperar, publicar. Devuelve el media id publicado."""
    container_id = create_media_container(image_url, caption=caption)
    wait_until_container_ready(container_id)
    return publish_container(container_id)
