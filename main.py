"""
Script principal. Pensado para correr 4 veces por día vía GitHub Actions
(desayuno, almuerzo, merienda, cena).

En cada corrida:
  1) Busca imágenes nuevas en 'originales' que todavía no estén en 'editadas'.
     Para cada una, genera las 4 versiones FINALES (logo + banner) por franja
     horaria (desayuno/almuerzo/merienda/cena) y las sube a 'editadas', para
     que revises el resultado terminado antes de aprobar.
  2) Toma la imagen MÁS RECIENTE de 'aprobadas' (la carpeta donde vos movés a
     mano la versión específica que diste el OK), la publica en Instagram tal
     cual está, y la mueve a 'publicadas'.

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
    import os as _os
    originales = drive_utils.list_files(service, config.GDRIVE_FOLDER_ORIGINALES, config.VALID_EXTENSIONS)
    print(f"[editar] {len(originales)} archivo(s) en 'originales'.")

    nuevas = 0
    for f in originales:
        base_name, ext = _os.path.splitext(f["name"])
        slots_faltantes = [
            slot for slot in config.SLOT_STYLES
            if not drive_utils.file_exists_by_name(
                service, config.GDRIVE_FOLDER_EDITADAS, watermark.slot_suffix(base_name, ext, slot)
            )
        ]
        if not slots_faltantes:
            continue  # las 4 versiones de esta foto ya existen en 'editadas'

        print(f"[editar] Procesando '{f['name']}' (faltan: {', '.join(slots_faltantes)})...")
        original_bytes = drive_utils.download_file(service, f["id"])

        for slot in slots_faltantes:
            final_bytes = watermark.apply_full_design(original_bytes, slot)
            nombre_final = watermark.slot_suffix(base_name, ext, slot)
            drive_utils.upload_file(service, config.GDRIVE_FOLDER_EDITADAS, nombre_final, final_bytes)
            nuevas += 1

    print(f"[editar] {nuevas} imagen(es) nueva(s) generada(s) (4 por foto: desayuno/almuerzo/merienda/cena).")


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

    # La imagen en 'aprobadas' ya viene con logo + banner (se armó así en 'editadas').
    # La franja se detecta por el nombre de archivo (ej. 'foto_desayuno.jpg'); si no
    # se puede detectar, se usa la franja de la corrida actual como respaldo.
    slot = watermark.extract_slot_from_filename(siguiente["name"]) or os.environ.get("POST_SLOT")

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
