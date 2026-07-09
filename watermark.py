"""
Diseño de flyer estilo "póster" para Sandwichería FIORE Confitería (v2).

Inspirado en las piezas promocionales de la marca:
  - Logo grande centrado arriba, con sombra.
  - Titular en tipografía condensada pesada (Anton), en MAYÚSCULAS, sobre
    cintas de color inclinadas y superpuestas (con sombra dura, estilo póster).
  - Subtítulo en una cinta oscura más chica.
  - Acento manuscrito (Pacifico) con la localidad.
  - Píldora blanca abajo con corazón + "Hecho en casa, todos los días".

Las frases rotan: cada foto elige (de forma determinística según su nombre)
una frase distinta de la lista de su franja, así los posts no se repiten.

Funciones usadas por main.py: apply_full_design(), slot_suffix(),
extract_slot_from_filename(), slots_for_filename().
"""

import io
import zlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import config

SLOTS = ("desayuno", "almuerzo", "merienda", "cena")

# ------------------------------------------------------------------
# Fuentes
# ------------------------------------------------------------------

_FALLBACK_FONT_PATHS = [
    "assets/fonts/Poppins-Bold.ttf",
    "assets/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

_HEADLINE_FONT_PATH = getattr(config, "FLYER_HEADLINE_FONT_PATH_V2", "assets/fonts/Anton-Regular.ttf")
_SANS_FONT_PATH = getattr(config, "FLYER_SUBTITLE_FONT_PATH", "assets/fonts/Poppins-Bold.ttf")
_SCRIPT_FONT_PATH = getattr(config, "FLYER_SCRIPT_FONT_PATH", "assets/fonts/Pacifico-Regular.ttf")


def _load_font(preferred_path, size):
    """Intenta cargar la fuente preferida; si falla, prueba rutas de respaldo conocidas."""
    candidates = [preferred_path] + [p for p in _FALLBACK_FONT_PATHS if p != preferred_path]
    for path in candidates:
        try:
            font = ImageFont.truetype(path, size)
            if path != preferred_path:
                print(f"[watermark] Aviso: no se encontró '{preferred_path}', usando '{path}'.")
            return font
        except OSError:
            continue
    print("[watermark] Aviso: ninguna fuente .ttf encontrada, usando la fuente de emergencia de Pillow (chica).")
    return ImageFont.load_default()


def _fit_font(preferred_path, text, max_width, start_size, min_size=14):
    size = start_size
    while size > min_size:
        font = _load_font(preferred_path, size)
        bbox = font.getbbox(text)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size = int(size * 0.94)
    return _load_font(preferred_path, min_size)


# ------------------------------------------------------------------
# Paleta de la marca y estilo por franja
# ------------------------------------------------------------------

ROJO = (166, 25, 46, 255)
VERDE = (30, 113, 69, 255)
DORADO = (212, 160, 23, 255)
OSCURO = (24, 24, 26, 255)
BLANCO = (255, 255, 255, 255)
CREMA = (250, 246, 238, 255)

_SLOT_THEME = {
    #             cinta 1              cinta 2 (invertida)    cinta subtítulo
    "desayuno": {"c1": DORADO, "t1": OSCURO, "c2": CREMA, "t2": ROJO,   "c3": VERDE,  "t3": BLANCO},
    "almuerzo": {"c1": ROJO,   "t1": BLANCO, "c2": CREMA, "t2": ROJO,   "c3": OSCURO, "t3": DORADO},
    "merienda": {"c1": VERDE,  "t1": BLANCO, "c2": CREMA, "t2": VERDE,  "c3": ROJO,   "t3": BLANCO},
    "cena":     {"c1": OSCURO, "t1": DORADO, "c2": CREMA, "t2": OSCURO, "c3": ROJO,   "t3": BLANCO},
}

# ------------------------------------------------------------------
# Frases por franja: (titular, subtítulo). El titular va en MAYÚSCULAS
# en la cinta grande; el subtítulo en la cinta chica. Se pueden pisar
# desde config.py con FLYER_PHRASES = {"desayuno": [("...", "..."), ...], ...}
# ------------------------------------------------------------------

_DEFAULT_PHRASES = {
    "desayuno": [
        ("¡Buen día!", "Arrancá la mañana con algo rico"),
        ("Algo rico", "y buena compañía te esperan"),
        ("¡A desayunar!", "como corresponde"),
        ("El mejor comienzo", "del día empieza acá"),
        ("¡Buen día!", "Vení a desayunar con nosotros"),
        ("Mate o café", "¡pero con algo dulce al lado!"),
        ("Arrancamos el día", "juntos — ¡te esperamos!"),
        ("Buen desayuno", "para empezar bien el día"),
    ],
    "almuerzo": [
        ("¿Qué almorzás hoy?", "Nosotros te resolvemos"),
        ("Hora de almorzar", "rico y sin vueltas"),
        ("¡El almuerzo ya está!", "Vení a buscarlo"),
        ("Al mediodía", "lo mejor es comer bien"),
        ("¿Hambre?", "Tenemos la solución"),
        ("Buen almuerzo", "te esperamos hoy"),
        ("Pausa del mediodía", "¡a comer algo rico!"),
        ("El almuerzo de hoy", "tiene tu nombre"),
    ],
    "merienda": [
        ("¡Hora de la merienda!", "te esperamos con algo rico"),
        ("Algo dulce", "a esta hora cae perfecto"),
        ("Merienda y charla", "el combo ideal"),
        ("¡A merendar!", "vení por algo rico"),
        ("La tarde pide", "una buena merienda"),
        ("Café, té y algo dulce", "¿te sumás?"),
        ("El mimo de la tarde", "¡a merendar!"),
        ("Tarde completa", "con una buena merienda"),
    ],
    "cena": [
        ("¿Qué cenás hoy?", "Nosotros te ayudamos"),
        ("Hora de cenar rico", "sin complicarte"),
        ("¡Te esperamos!", "para cenar algo rico"),
        ("Cerrá el día", "con una buena cena"),
        ("¿Hambre de noche?", "Tenemos lo que buscás"),
        ("La cena ya está", "lista para vos"),
        ("Una buena comida", "para terminar el día"),
        ("¡A cenar se ha dicho!", "te esperamos"),
    ],
}


def _pick_phrase(slot, seed_name=""):
    """Elige una frase de la franja. Con seed_name (nombre del archivo) la
    elección es determinística: la misma foto siempre lleva la misma frase,
    pero fotos distintas llevan frases distintas."""
    phrases = getattr(config, "FLYER_PHRASES", _DEFAULT_PHRASES).get(slot) or _DEFAULT_PHRASES["almuerzo"]
    idx = zlib.crc32(seed_name.encode("utf-8")) % len(phrases) if seed_name else 0
    return phrases[idx]


_DULCE = ["desayuno", "merienda"]
_SALADO = ["almuerzo", "cena"]

_DEFAULT_PRODUCT_SLOTS = {
    # dulces / panificados -> desayuno y merienda
    "dulce":     _DULCE,      # dulces, membrillo dulce
    "alfajor":   _DULCE,
    "torta":     _DULCE,
    "medialun":  _DULCE,      # medialunas (las saladas se detectan aparte)
    "factur":    _DULCE,
    "chipa":     _DULCE,
    "arrollad":  _DULCE,      # arrollado (el salado se detecta aparte)
    "bombon":    _DULCE,
    "masas":     _DULCE,      # masas, masas secas, masas finas
    "masitas":   _DULCE,
    "budin":     _DULCE,
    "galletita": _DULCE,
    "membrillo": _DULCE,
    "pastelito": _DULCE,
    "palito":    _DULCE,      # palito salado
    # salados -> almuerzo y cena
    "sandwich":  _SALADO,
    "sanwich":   _SALADO,     # variante sin la primera d
    "sanguch":   _SALADO,
    "empanad":   _SALADO,
    "tarta":     _SALADO,     # tarta salada
    "pizzeta":   _SALADO,
    "pizza":     _SALADO,
    "calzon":    _SALADO,     # calzon, calzones, calzone
    "katering":  _SALADO,
    "catering":  _SALADO,
    "fosforito": _SALADO,
}

# Combinaciones específicas: si TODAS las partes aparecen en el nombre, mandan
# sobre la palabra genérica (ej: 'medialunas saladas' le gana a 'medialunas').
_SPECIFIC_PRODUCTS = [
    (("medialun", "salad"), _SALADO),   # medialunas saladas
    (("arrollad", "salad"), _SALADO),   # arrollado salado
]


def _normalize(text):
    """minúsculas, sin tildes y con separadores como espacios."""
    import unicodedata
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    for sep in "_-.":
        text = text.replace(sep, " ")
    return text


def slots_for_filename(filename):
    """
    Devuelve las franjas a generar para una foto original según el producto
    que mencione su nombre (ej: 'empanadas_carne.jpg' -> ['almuerzo', 'cena']).
    Si no se reconoce ningún producto, devuelve las 4 franjas.
    """
    mapping = getattr(config, "PRODUCT_SLOTS", _DEFAULT_PRODUCT_SLOTS)
    name = _normalize(filename)

    matched = set()
    suppressed = set()
    for parts, slots in _SPECIFIC_PRODUCTS:
        if all(part in name for part in parts):
            matched.update(slots)
            suppressed.add(parts[0])  # no evaluar la palabra genérica

    for keyword, slots in mapping.items():
        kw = _normalize(keyword)
        if kw in suppressed:
            continue
        if kw in name:
            matched.update(slots)

    if not matched:
        return list(SLOTS)
    return [s for s in SLOTS if s in matched]



# ------------------------------------------------------------------
# Nombres de archivo por franja
# ------------------------------------------------------------------

def slot_suffix(base_name, ext, slot):
    """'foto', '.jpg', 'almuerzo' -> 'foto_almuerzo.jpg'"""
    return f"{base_name}_{slot}{ext}"


def extract_slot_from_filename(filename):
    """Devuelve la franja detectada en el nombre de archivo, o None."""
    lower = filename.lower()
    for slot in SLOTS:
        if slot in lower:
            return slot
    return None


# ------------------------------------------------------------------
# Piezas del diseño
# ------------------------------------------------------------------

def _ref(base):
    """Dimensión de referencia para escalar (soporta fotos apaisadas)."""
    W, H = base.size
    return min(W, int(H * 0.8))


def _paste_logo_center(base):
    """Logo grande centrado arriba, con sombra suave (sin tarjeta blanca)."""
    W, H = base.size
    ref = _ref(base)
    logo = Image.open(config.LOGO_PATH).convert("RGBA")
    target_w = int(ref * getattr(config, "FLYER_LOGO_WIDTH_RATIO_V2", 0.40))
    ratio = target_w / logo.width
    logo = logo.resize((target_w, int(logo.height * ratio)), Image.LANCZOS)

    # sombra: silueta del logo desplazada y difuminada
    alpha = logo.split()[3]
    shadow = Image.new("RGBA", logo.size, (0, 0, 0, 0))
    shadow.putalpha(alpha.point(lambda a: int(a * 0.55)))
    blur = max(3, int(ref * 0.010))
    canvas = Image.new("RGBA", (logo.width + blur * 6, logo.height + blur * 6), (0, 0, 0, 0))
    canvas.alpha_composite(shadow, (blur * 3 + int(ref * 0.006), blur * 3 + int(ref * 0.010)))
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(logo, (blur * 3, blur * 3))

    y = int(ref * 0.025)
    base.alpha_composite(canvas, ((W - canvas.width) // 2, y))
    return y + canvas.height - blur * 3  # borde inferior aprox del logo


def _ribbon(base, text, font, x, y, bg, fg, angle=-2.5, pad_x_ratio=0.55, pad_y_ratio=0.30):
    """Cinta de color inclinada con sombra dura (estilo póster) y texto adentro.
    Devuelve la altura efectiva ocupada (para apilar la siguiente cinta)."""
    ref = _ref(base)
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = int(th * pad_x_ratio), int(th * pad_y_ratio)
    w, h = tw + pad_x * 2, th + pad_y * 2
    off = max(3, int(ref * 0.008))  # sombra dura desplazada

    layer = Image.new("RGBA", (w + off * 3, h + off * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = max(2, int(h * 0.10))
    d.rounded_rectangle([off, off, off + w, off + h], radius=r, fill=(15, 15, 17, 200))  # sombra
    d.rounded_rectangle([0, 0, w, h], radius=r, fill=bg)
    d.text((pad_x - bbox[0], pad_y - bbox[1]), text, font=font, fill=fg)

    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)

    base.alpha_composite(layer, (x, y))
    return int(layer.height * 0.82)  # solapado leve entre cintas


def _split_headline(text, font_path, max_width, size):
    """Si el titular no entra en una línea con buen tamaño, lo parte en dos."""
    font = _load_font(font_path, size)
    bbox = font.getbbox(text)
    if bbox[2] - bbox[0] <= max_width:
        return [text]
    words = text.split()
    if len(words) < 2:
        return [text]
    best, best_diff = 1, None
    for i in range(1, len(words)):
        l1, l2 = " ".join(words[:i]), " ".join(words[i:])
        diff = abs(len(l1) - len(l2))
        if best_diff is None or diff < best_diff:
            best, best_diff = i, diff
    return [" ".join(words[:best]), " ".join(words[best:])]


def _draw_script_accent(base, text, x, y):
    """Línea manuscrita (Pacifico) con sombra, estilo firma."""
    ref = _ref(base)
    font = _fit_font(_SCRIPT_FONT_PATH, text, base.width * 0.7, int(ref * 0.055))
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = int(th * 0.5)
    layer = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    o = max(2, int(ref * 0.004))
    d.text((pad - bbox[0] + o, pad - bbox[1] + o), text, font=font, fill=(0, 0, 0, 190))
    layer = layer.filter(ImageFilter.GaussianBlur(max(2, int(ref * 0.005))))
    d = ImageDraw.Draw(layer)
    d.text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=BLANCO)
    base.alpha_composite(layer, (x, y))
    return layer.height


def _draw_heart(draw, cx, cy, size, color):
    r = size / 4
    draw.ellipse([cx - 2 * r, cy - 2 * r, cx, cy], fill=color)
    draw.ellipse([cx, cy - 2 * r, cx + 2 * r, cy], fill=color)
    draw.polygon([(cx - 2 * r, cy - r * 0.6), (cx + 2 * r, cy - r * 0.6), (cx, cy + 2 * r)], fill=color)


def _draw_footer_pill(base, text):
    """Píldora blanca semitransparente abajo, con corazón rojo + texto."""
    W, H = base.size
    ref = _ref(base)
    font = _fit_font(_SANS_FONT_PATH, text, W * 0.72, int(ref * 0.033))
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    heart = int(th * 0.9)
    gap = int(th * 0.5)
    pad_x, pad_y = int(th * 1.0), int(th * 0.55)
    pill_w = heart + gap + tw + pad_x * 2
    pill_h = th + pad_y * 2
    radius = pill_h // 2

    pill = Image.new("RGBA", (pill_w + 12, pill_h + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(pill)
    d.rounded_rectangle([4, 6, 4 + pill_w, 6 + pill_h], radius=radius, fill=(0, 0, 0, 90))
    pill = pill.filter(ImageFilter.GaussianBlur(3))
    d = ImageDraw.Draw(pill)
    d.rounded_rectangle([2, 2, 2 + pill_w, 2 + pill_h], radius=radius, fill=(255, 255, 255, 228))
    _draw_heart(d, 2 + pad_x + heart // 2, 2 + pill_h // 2, heart, ROJO)
    d.text((2 + pad_x + heart + gap - bbox[0], 2 + pad_y - bbox[1]), text, font=font, fill=(45, 40, 38, 255))

    base.alpha_composite(pill, ((W - pill.width) // 2, int(H - pill.height - H * 0.030)))


# ------------------------------------------------------------------
# Diseño completo
# ------------------------------------------------------------------

def apply_full_design(image_bytes, slot, seed_name=""):
    """
    Aplica el diseño estilo póster sobre la foto original y devuelve los bytes
    JPEG listos para subir a 'editadas'. seed_name (el nombre del archivo
    original) define qué frase de la franja se usa, para variar entre fotos.
    """
    slot = slot or "almuerzo"
    theme = _SLOT_THEME.get(slot, _SLOT_THEME["almuerzo"])
    headline, subtitle = _pick_phrase(slot, seed_name)

    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    W, H = img.size
    ref = _ref(img)

    logo_bottom = _paste_logo_center(img)

    # --- bloque de cintas, alineado a la izquierda como en los pósters ---
    x = int(W * 0.055)
    y = logo_bottom + int(ref * 0.030)
    max_w = int(W * 0.86)

    head_size = int(ref * 0.105)
    lines = _split_headline(headline.upper(), _HEADLINE_FONT_PATH, max_w - int(head_size * 1.1), head_size)
    for i, line in enumerate(lines):
        font = _fit_font(_HEADLINE_FONT_PATH, line, max_w - int(head_size * 1.1), head_size)
        bg, fg = (theme["c1"], theme["t1"]) if i % 2 == 0 else (theme["c2"], theme["t2"])
        used = _ribbon(img, line, font, x + i * int(ref * 0.030), y, bg, fg)
        y += used

    sub_font = _fit_font(_SANS_FONT_PATH, subtitle.upper(), max_w * 0.9, int(ref * 0.037))
    used = _ribbon(img, subtitle.upper(), sub_font, x + int(ref * 0.015), y + int(ref * 0.006),
                   theme["c3"], theme["t3"], pad_x_ratio=0.75, pad_y_ratio=0.45)
    y += used + int(ref * 0.014)

    accent = getattr(config, "FLYER_ACCENT_TEXT", "Lomas de Zamora")
    if accent:
        _draw_script_accent(img, accent, x + int(ref * 0.05), y)

    footer = getattr(config, "FLYER_FOOTER_TEXT", "Hecho en casa, todos los días")
    if footer:
        _draw_footer_pill(img, footer)

    out = io.BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=92)
    return out.getvalue()
