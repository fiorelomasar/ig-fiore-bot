"""
Script principal. Pensado para correr 4 veces por día vía GitHub Actions
(desayuno, almuerzo, merienda, cena).

En cada corrida:
  1) Busca imágenes nuevas en 'originales' que todavía no estén en 'editadas',
     les aplica la marca de agua y las sube a 'editadas' (para que las revises).
  2) Toma la imagen MÁS RECIENTE de 'aprobadas' (la carpeta donde vos movés a mano
     las que diste el OK), le agrega el banner de la franja horaria actual,
     la publica en Instagram, y la mueve a 'publicadas'.

El bot nunca publica nada de 'editadas' directamente: solo publica lo que vos
movés manualmente a 'aprobadas' en Google Drive. Ese movimiento ES el paso de
aprobación.
"""

import os
import sys

import config
import drive_utils
import watermark
import instagram_api
import temp_hosting


def editar_imagenes_nuevas(service):
    originales = drive_utils.list_files(service, config.GDRIVE_FOLDER_ORIGINALES, config.VALID_EXTENSIONS)
    print(f"[editar] {len(originales)} archivo(s) en 'originales'.")

    nuevas = 0
    for f in originales:
        if drive_utils.file_exists_by_name(service, config.GDRIVE_FOLDER_EDITADAS, f["name"]):
            continue  # ya fue editada antes

        print(f"[editar] Procesando '{f['name']}'...")
        original_bytes = drive_utils.download_file(service, f["id"])
        edited_bytes = watermark.apply_watermark(original_bytes)
        drive_utils.upload_file(service, config.GDRIVE_FOLDER_EDITADAS, f["name"], edited_bytes)
        nuevas += 1

    print(f"[editar] {nuevas} imagen(es) nueva(s) editada(s).")


def publicar_siguiente(service):
    aprobadas = drive_utils.list_files(service, config.GDRIVE_FOLDER_APROBADAS, config.VALID_EXTENSIONS)
    if not aprobadas:
        print("[publicar] No hay imágenes pendientes en 'aprobadas'.")
        return

    # Más reciente primero: la última que aprobaste es la próxima en publicarse.
    aprobadas.sort(key=lambda f: f["createdTime"], reverse=True)
    siguiente = aprobadas[0]
    print(f"[publicar] Publicando '{siguiente['name']}' (la más reciente de 'aprobadas')...")

    content_bytes = drive_utils.download_file(service, siguiente["id"])

    slot = os.environ.get("POST_SLOT")  # "desayuno" | "almuerzo" | "merienda" | "cena"
    content_bytes = watermark.apply_flyer_banner(content_bytes, slot)

    public_url = temp_hosting.publish_to_temp_hosting(siguiente["name"], content_bytes)
    print(f"[publicar] Imagen disponible temporalmente en: {public_url}")

    try:
        caption = config.get_caption(slot)
        media_id = instagram_api.publish_image(public_url, caption=caption)
        print(f"[publicar] ¡Publicado en Instagram! (franja: {slot}) media_id={media_id}")
    finally:
        temp_hosting.remove_from_temp_hosting(siguiente["name"])

    drive_utils.move_file(service, siguiente["id"], config.GDRIVE_FOLDER_PUBLICADAS)
    print(f"[publicar] Movida a 'publicadas' en Drive.")


def main():
    service = drive_utils.get_drive_service()
    editar_imagenes_nuevas(service)
    publicar_siguiente(service)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
