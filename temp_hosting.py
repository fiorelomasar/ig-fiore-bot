"""
"Hosting" temporal: copia la imagen elegida dentro del repo (carpeta temp_hosting/),
hace commit y push, y devuelve la URL pública en raw.githubusercontent.com.

Requiere que el repo sea PÚBLICO (o que uses GitHub Pages) para que Instagram
pueda descargar la imagen sin autenticación.
"""

import os
import subprocess

import config


def _run(cmd):
    subprocess.run(cmd, check=True)


def publish_to_temp_hosting(filename, content_bytes):
    """Guarda la imagen en temp_hosting/, la commitea y pushea. Devuelve la URL pública raw."""
    os.makedirs(config.TEMP_HOSTING_DIR, exist_ok=True)
    local_path = os.path.join(config.TEMP_HOSTING_DIR, filename)
    with open(local_path, "wb") as f:
        f.write(content_bytes)

    _run(["git", "config", "user.name", "ig-confiteria-bot"])
    _run(["git", "config", "user.email", "bot@users.noreply.github.com"])
    _run(["git", "add", local_path])
    _run(["git", "commit", "-m", f"temp hosting: {filename}"])
    _run(["git", "push"])

    repo = config.GITHUB_REPO
    branch = config.GITHUB_BRANCH
    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{config.TEMP_HOSTING_DIR}/{filename}"
    return raw_url


def remove_from_temp_hosting(filename):
    """Borra la imagen temporal del repo una vez publicada en Instagram, y pushea el cambio."""
    local_path = os.path.join(config.TEMP_HOSTING_DIR, filename)
    if os.path.exists(local_path):
        os.remove(local_path)
        _run(["git", "add", local_path])
        _run(["git", "commit", "-m", f"cleanup temp hosting: {filename}"])
        _run(["git", "push"])
