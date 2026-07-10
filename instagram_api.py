"""
Publicación en Instagram usando la Graph API de Meta.
Flujo: crear "media container" con la URL pública de la imagen -> publicarlo.
"""

import time
import requests

import config

GRAPH_BASE = f"https://graph.facebook.com/{config.GRAPH_API_VERSION}"


def _check(resp):
    """raise_for_status pero mostrando el mensaje de error real de Meta,
    que explica el motivo (proporción inválida, token vencido, etc.)."""
    if resp.status_code >= 400:
        try:
            detalle = resp.json().get("error", {})
            msg = detalle.get("message", resp.text)
            sub = detalle.get("error_user_msg") or detalle.get("error_user_title") or ""
            print(f"[instagram] Error de la API de Meta: {msg} {('| ' + sub) if sub else ''}")
        except Exception:
            print(f"[instagram] Error de la API de Meta (sin detalle JSON): {resp.text[:500]}")
    resp.raise_for_status()


def create_media_container(image_url, caption=None, es_historia=False):
    url = f"{GRAPH_BASE}/{config.IG_USER_ID}/media"
    payload = {
        "image_url": image_url,
        "access_token": config.IG_ACCESS_TOKEN,
    }
    if es_historia:
        # Las historias no llevan caption y requieren media_type=STORIES
        payload["media_type"] = "STORIES"
    else:
        payload["caption"] = caption or config.DEFAULT_CAPTION
    resp = requests.post(url, data=payload, timeout=60)
    _check(resp)
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
        _check(resp)
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
    _check(resp)
    return resp.json()["id"]


def publish_image(image_url, caption=None, es_historia=False):
    """Orquesta el flujo completo: crear container, esperar, publicar.
    Con es_historia=True publica como historia (24 hs) en vez de post del feed.
    Devuelve el media id publicado."""
    tipo = "historia" if es_historia else "post"
    print(f"[instagram] Publicando como {tipo}...")
    container_id = create_media_container(image_url, caption=caption, es_historia=es_historia)
    wait_until_container_ready(container_id)
    return publish_container(container_id)
