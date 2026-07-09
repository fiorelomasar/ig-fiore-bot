"""
Configuración del bot de publicación en Instagram.
Editá estos valores según tu negocio. No hace falta tocar el resto del código.
"""

import os

# ------------------------------------------------------------------
# NEGOCIO / MARCA DE AGUA
# ------------------------------------------------------------------

# Nombre que se va a mostrar en la marca de agua (si usás modo "text")
BUSINESS_NAME = "Sandwichería y Confitería FIORE"

# Modo de marca de agua: "text" (escribe el nombre) o "logo" (superpone un PNG)
WATERMARK_MODE = "logo"  # "text" | "logo"

# Si WATERMARK_MODE = "logo", ruta al archivo del logo (PNG con transparencia recomendado)
LOGO_PATH = "assets/logo.png"

# Posición: "bottom-right", "bottom-left", "top-right", "top-left", "center"
# Elegido "top-left" para que quede parecido a tus flyers actuales (logo arriba a la izquierda)
WATERMARK_POSITION = "top-left"

# Margen en píxeles respecto al borde
WATERMARK_MARGIN = 30

# --- Solo para modo "text" ---
FONT_PATH = "assets/font.ttf"          # Poné una tipografía .ttf en assets/ (ver README)
FONT_SIZE_RATIO = 0.045                # Tamaño de fuente relativo al ancho de la imagen
TEXT_COLOR = (255, 255, 255, 255)      # RGBA, blanco
TEXT_STROKE_COLOR = (0, 0, 0, 180)     # Contorno para que se lea sobre cualquier fondo
TEXT_STROKE_WIDTH = 2

# Franja de fondo semi-transparente detrás del texto (mejora legibilidad). None para desactivar.
TEXT_BACKGROUND_COLOR = (0, 0, 0, 110)  # RGBA
TEXT_BACKGROUND_PADDING = 14

# --- Solo para modo "logo" ---
LOGO_WIDTH_RATIO = 0.20  # el logo ocupa el 20% del ancho de la imagen, se escala manteniendo proporción
LOGO_OPACITY = 0.95      # 0.0 a 1.0

# Chip blanco redondeado detrás del logo (igual que en tus flyers actuales). None para desactivar.
LOGO_BACKGROUND_COLOR = (255, 255, 255, 235)  # RGBA
LOGO_BACKGROUND_PADDING = 14
LOGO_BACKGROUND_RADIUS = 16

# ------------------------------------------------------------------
# GOOGLE DRIVE
# ------------------------------------------------------------------

# IDs de las carpetas de Drive (se obtienen de la URL de cada carpeta)
GDRIVE_FOLDER_ORIGINALES = os.environ.get("GDRIVE_FOLDER_ORIGINALES", "")
GDRIVE_FOLDER_EDITADAS = os.environ.get("GDRIVE_FOLDER_EDITADAS", "")
GDRIVE_FOLDER_APROBADAS = os.environ.get("GDRIVE_FOLDER_APROBADAS", "")
GDRIVE_FOLDER_PUBLICADAS = os.environ.get("GDRIVE_FOLDER_PUBLICADAS", "")

# Extensiones de imagen que el bot va a procesar
VALID_EXTENSIONS = (".jpg", ".jpeg", ".png")

# ------------------------------------------------------------------
# INSTAGRAM GRAPH API
# ------------------------------------------------------------------

IG_USER_ID = os.environ.get("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
GRAPH_API_VERSION = "v19.0"

# Opcional: caption fijo o por defecto si no se especifica otro mecanismo
DEFAULT_CAPTION = f"{BUSINESS_NAME} 🍰 #confiteria #reposteria"

# Captions según la franja horaria del posteo (ver POST_SLOT en el workflow de GitHub Actions).
# El bot elige una al azar de la lista correspondiente en cada corrida, para variar un poco.
CAPTIONS = {
    "desayuno": [
        f"¡Buen día, Lomas! ☀️ Arrancá la mañana como se debe, con lo mejor de {BUSINESS_NAME} 🥐☕ #desayuno #LomasDeZamora",
        f"Café calentito y algo rico recién horneado. Así arranca el día en {BUSINESS_NAME} ☕🥐 #desayuno",
        f"El desayuno perfecto está más cerca de lo que pensás 😉☕ {BUSINESS_NAME} #desayuno #buendia",
    ],
    "almuerzo": [
        f"¿Ya pensaste qué almorzar? Te lo resolvemos nosotros 😋 {BUSINESS_NAME} #almuerzo #LomasDeZamora",
        f"Hora del almuerzo. Sanguches frescos, todos los días, en {BUSINESS_NAME} 🥪 #almuerzo",
        f"Mediodía = hambre. Pasá por {BUSINESS_NAME} y solucionalo 🙌 #almuerzo #sandwicheria",
    ],
    "merienda": [
        f"La merienda no se negocia ☕🍰 Te esperamos en {BUSINESS_NAME} #merienda #LomasDeZamora",
        f"Algo dulce para la tarde, como a vos te gusta 🍰☕ {BUSINESS_NAME} #merienda",
        f"Pausa de la tarde con la mejor merienda del barrio en {BUSINESS_NAME} 🍰 #merienda",
    ],
    "cena": [
        f"Para la cena de esta noche, {BUSINESS_NAME} tiene la posta 🌙🥪 #cena #LomasDeZamora",
        f"¿Qué comemos hoy? Fácil: algo de {BUSINESS_NAME} 🌙 #cena #sandwicheria",
        f"Cerrá el día como se merece, con {BUSINESS_NAME} 🌙🍰 #cena",
    ],
}

# ------------------------------------------------------------------
# HOSTING TEMPORAL DE IMÁGENES (para que Instagram pueda descargarlas)
# ------------------------------------------------------------------

# Carpeta del propio repo donde se copia temporalmente la imagen a publicar
# Requiere que el repo sea PÚBLICO para que raw.githubusercontent.com funcione sin login.
TEMP_HOSTING_DIR = "temp_hosting"
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "")  # ej: "usuario/ig-confiteria-bot"
GITHUB_BRANCH = os.environ.get("GITHUB_REF_NAME", "main")


def get_caption(slot=None):
    """
    Devuelve un caption acorde a la franja horaria ('desayuno', 'almuerzo', 'merienda', 'cena').
    Si no se especifica o no se reconoce, usa DEFAULT_CAPTION.
    """
    import random
    if slot and slot in CAPTIONS:
        return random.choice(CAPTIONS[slot])
    return DEFAULT_CAPTION


# ------------------------------------------------------------------
# BANNER DE FLYER POR FRANJA HORARIA (se aplica recién al publicar)
# ------------------------------------------------------------------

# Activar/desactivar el banner inferior tipo flyer (además del logo de editadas)
FLYER_BANNER_ENABLED = True

# Altura del banner como proporción de la altura de la imagen
FLYER_BANNER_HEIGHT_RATIO = 0.22

# Fuentes para el banner (dejar como están si no subiste otras a assets/)
FLYER_HEADLINE_FONT_PATH = "assets/fonts/Poppins-Bold.ttf"
FLYER_SUBTITLE_FONT_PATH = "assets/fonts/Poppins-Bold.ttf"

SLOT_STYLES = {
    "desayuno": {
        "bg_color": (212, 160, 23, 235),      # dorado, como los "30% OFF" de tus flyers
        "text_color": (40, 25, 5, 255),
        "headline": "¡A DESAYUNAR!",
    },
    "almuerzo": {
        "bg_color": (166, 25, 46, 235),        # rojo del logo
        "text_color": (255, 255, 255, 255),
        "headline": "HORA DEL ALMUERZO",
    },
    "merienda": {
        "bg_color": (30, 113, 69, 235),        # verde del logo
        "text_color": (255, 255, 255, 255),
        "headline": "MOMENTO MERIENDA",
    },
    "cena": {
        "bg_color": (20, 20, 22, 235),         # oscuro, clima nocturno
        "text_color": (212, 160, 23, 255),     # texto dorado sobre fondo oscuro
        "headline": "PARA LA CENA",
    },
}

FLYER_SUBTITLE_TEXT = f"{BUSINESS_NAME} · Lomas de Zamora"
