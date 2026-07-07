"""
Diseño de flyer estilo "historia de Instagram" para Sandwichería FIORE Confitería.

Genera, sobre la foto original:
  1. Logo arriba a la izquierda, en una tarjeta blanca redondeada con sombra suave.
  2. Titular grande en tipografía manuscrita (Pacifico), blanco con sombra difusa.
  3. Píldora de color (según franja horaria) con el subtítulo.
  4. Línea chica opcional debajo ("Te esperamos en Fiore").
  5. Píldora blanca semitransparente abajo con un corazón rojo y el texto
     "Hecho en casa, todos los días".

Funciones usadas por main.py: apply_full_design(), slot_suffix(),
extract_slot_from_filename().

Todos los textos y colores se pueden pisar desde config.py (ver README /
snippet FLYER_TEXTS); si no existen, se usan los valores por defecto de acá.
"""

import io
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import config

SLOTS = ("desayuno", "almuerzo", "merienda", "cena")

# ------------------------------------------------------------------
# Fuentes
# ------------------------------------------------------------------

# Rutas de respaldo si una fuente no se encuentra (evita caer en la fuente
# de emergencia de Pillow, que es diminuta e ilegible).
_FALLBACK_FONT_PATHS = [
    "assets/fonts/Poppins-Bold.ttf",
    "assets/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

_SCRIPT_FONT_PATH = getattr(config, "FLYER_SCRIPT_FONT_PATH", "assets/fonts/Pacifico-Regular.ttf")
_SANS_FONT_PATH = getattr(config, "FLYER_SUBTITLE_FONT_PATH", "assets/fonts/Poppins-Bold.ttf")


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
    """Achica la fuente hasta que el texto entre en max_width."""
    size = start_size
    while size > min_size:
        font = _load_font(preferred_path, size)
        if _text_size(text, font)[0] <= max_width:
            return font
        size = int(size * 0.94)
    return _load_font(preferred_path, min_size)


def _text_size(text, font):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


# ------------------------------------------------------------------
# Contenido por franja (colores tomados de config.SLOT_STYLES si existen)
# ------------------------------------------------------------------

_DEFAULT_TEXTS = {
    "desayuno": {
        "headline": "Buen día",
        "subtitle": "Arrancá el día con algo rico",
    },
    "almuerzo": {
        "headline": "Para almorzar",
        "subtitle": "rico, casero y fresco",
    },
    "merienda": {
        "headline": "La merienda",
        "subtitle": "dulce o salado, como quieras",
    },
    "cena": {
        "headline": "Para la cena",
        "subtitle": "cerrá el día con algo rico",
    },
}

_DEFAULT_COLORS = {
    "desayuno": {"bg_color": (212, 160, 23, 235), "text_color": (40, 25, 5, 255)},
    "almuerzo": {"bg_color": (166, 25, 46, 235), "text_color": (255, 255, 255, 255)},
    "merienda": {"bg_color": (30, 113, 69, 235), "text_color": (255, 255, 255, 255)},
    "cena": {"bg_color": (20, 20, 22, 235), "text_color": (212, 160, 23, 255)},
}


def _slot_style(slot):
    """Combina textos y colores: config.FLYER_TEXTS > config.SLOT_STYLES > defaults."""
    style = dict(_DEFAULT_COLORS.get(slot, _DEFAULT_COLORS["almuerzo"]))
    style.update(_DEFAULT_TEXTS.get(slot, _DEFAULT_TEXTS["almuerzo"]))

    cfg_colors = getattr(config, "SLOT_STYLES", {}).get(slot, {})
    for key in ("bg_color", "text_color"):
        if key in cfg_colors:
            style[key] = cfg_colors[key]

    cfg_texts = getattr(config, "FLYER_TEXTS", {}).get(slot, {})
    style.update(cfg_texts)
    return style


# ------------------------------------------------------------------
# Mapeo producto -> franjas horarias
# ------------------------------------------------------------------
# Si el nombre del archivo original menciona un producto conocido, solo se
# generan las versiones de las franjas que tienen sentido para ese producto.
# Si no se reconoce ninguno, se generan las 4. Se puede pisar desde config.py
# definiendo PRODUCT_SLOTS con el mismo formato.

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
    """Dimensión de referencia para escalar el diseño: evita textos gigantes
    en fotos apaisadas (usa la menor entre el ancho y el 80%% del alto)."""
    W, H = base.size
    return min(W, int(H * 0.8))


def _rounded_shadow_card(size, radius, blur, alpha=90):
    """Sombra suave para tarjetas/píldoras."""
    pad = blur * 3
    shadow = Image.new("RGBA", (size[0] + pad * 2, size[1] + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow)
    d.rounded_rectangle([pad, pad, pad + size[0], pad + size[1]], radius=radius, fill=(0, 0, 0, alpha))
    return shadow.filter(ImageFilter.GaussianBlur(blur)), pad


def _paste_logo_card(base):
    """Logo en tarjeta blanca redondeada, arriba a la izquierda."""
    W, H = base.size
    ref = _ref(base)
    margin = int(ref * 0.045)
    card_w = int(ref * getattr(config, "FLYER_LOGO_WIDTH_RATIO", 0.24))

    logo = Image.open(config.LOGO_PATH).convert("RGBA")
    inner_w = int(card_w * 0.86)
    ratio = inner_w / logo.width
    logo = logo.resize((inner_w, int(logo.height * ratio)), Image.LANCZOS)

    pad = int(card_w * 0.07)
    card_h = logo.height + pad * 2
    radius = int(card_w * 0.16)

    shadow, spad = _rounded_shadow_card((card_w, card_h), radius, blur=max(2, int(ref * 0.008)))
    base.alpha_composite(shadow, (margin - spad + int(ref * 0.004), margin - spad + int(ref * 0.006)))

    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=radius, fill=(255, 255, 255, 255))
    card.alpha_composite(logo, ((card_w - logo.width) // 2, pad))
    base.alpha_composite(card, (margin, margin))
    return margin + card_h  # borde inferior del logo, por si hace falta


def _draw_headline(base, text, y_center, min_top=0, angle_deg=-3):
    """Titular manuscrito blanco con sombra difusa, levemente inclinado.
    min_top: borde superior mínimo (para no pisar el logo en fotos apaisadas)."""
    W, _ = base.size
    ref = _ref(base)
    font = _fit_font(_SCRIPT_FONT_PATH, text, W * 0.88, int(ref * 0.125))
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    pad = int(th * 0.6)
    layer = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    origin = (pad - bbox[0], pad - bbox[1])

    # sombra difusa
    off = max(2, int(ref * 0.004))
    d.text((origin[0] + off, origin[1] + off), text, font=font, fill=(0, 0, 0, 190))
    layer = layer.filter(ImageFilter.GaussianBlur(max(2, int(ref * 0.006))))

    # texto principal
    d = ImageDraw.Draw(layer)
    d.text(origin, text, font=font, fill=(255, 255, 255, 255))

    if angle_deg:
        layer = layer.rotate(angle_deg, expand=True, resample=Image.BICUBIC)

    y = max(int(y_center - layer.height / 2), min_top)
    base.alpha_composite(layer, ((W - layer.width) // 2, y))
    return y + layer.height


def _draw_pill(base, text, y_top, bg_color, text_color, font_ratio=0.042):
    """Píldora redondeada centrada con texto."""
    W, _ = base.size
    ref = _ref(base)
    font = _fit_font(_SANS_FONT_PATH, text, W * 0.82, int(ref * font_ratio))
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    pad_x, pad_y = int(th * 1.1), int(th * 0.55)
    pill_w, pill_h = tw + pad_x * 2, th + pad_y * 2
    radius = pill_h // 2

    shadow, spad = _rounded_shadow_card((pill_w, pill_h), radius, blur=max(2, int(ref * 0.006)), alpha=70)
    x = (W - pill_w) // 2
    base.alpha_composite(shadow, (x - spad, y_top - spad + int(ref * 0.004)))

    pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(pill)
    d.rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], radius=radius, fill=bg_color)
    d.text((pad_x - bbox[0], pad_y - bbox[1]), text, font=font, fill=text_color)
    base.alpha_composite(pill, (x, y_top))
    return y_top + pill_h


def _draw_tagline(base, text, y_top):
    """Línea chica blanca con sombra, ej: '—  Te esperamos en Fiore  —'."""
    W, _ = base.size
    ref = _ref(base)
    font = _fit_font(_SANS_FONT_PATH, text, W * 0.8, int(ref * 0.028))
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    layer = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((10 - bbox[0] + 1, 10 - bbox[1] + 1), text, font=font, fill=(0, 0, 0, 170))
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    d = ImageDraw.Draw(layer)
    d.text((10 - bbox[0], 10 - bbox[1]), text, font=font, fill=(255, 255, 255, 255))
    base.alpha_composite(layer, ((W - layer.width) // 2, y_top))
    return y_top + layer.height


def _draw_heart(draw, cx, cy, size, color):
    """Corazón simple: dos círculos + triángulo."""
    r = size / 4
    draw.ellipse([cx - 2 * r, cy - 2 * r, cx, cy], fill=color)
    draw.ellipse([cx, cy - 2 * r, cx + 2 * r, cy], fill=color)
    draw.polygon(
        [(cx - 2 * r, cy - r * 0.6), (cx + 2 * r, cy - r * 0.6), (cx, cy + 2 * r)],
        fill=color,
    )


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

    pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(pill)
    d.rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], radius=radius, fill=(255, 255, 255, 225))
    _draw_heart(d, pad_x + heart // 2, pill_h // 2, heart, (166, 25, 46, 255))
    d.text((pad_x + heart + gap - bbox[0], pad_y - bbox[1]), text, font=font, fill=(45, 40, 38, 255))

    x = (W - pill_w) // 2
    y = int(H - pill_h - H * 0.035)
    shadow, spad = _rounded_shadow_card((pill_w, pill_h), radius, blur=max(2, int(ref * 0.005)), alpha=60)
    base.alpha_composite(shadow, (x - spad, y - spad + 2))
    base.alpha_composite(pill, (x, y))


# ------------------------------------------------------------------
# Diseño completo
# ------------------------------------------------------------------

def apply_full_design(image_bytes, slot):
    """
    Aplica el diseño completo (logo + titular + píldoras) sobre la foto original
    y devuelve los bytes JPEG listos para subir a 'editadas'.
    """
    style = _slot_style(slot or "almuerzo")

    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    W, H = img.size

    logo_bottom = _paste_logo_card(img)

    y = _draw_headline(
        img, style["headline"],
        y_center=int(H * 0.27),
        min_top=logo_bottom + int(_ref(img) * 0.015),
    )
    y = _draw_pill(
        img, style["subtitle"],
        y_top=y + int(H * 0.012),
        bg_color=style["bg_color"],
        text_color=style["text_color"],
    )

    tagline = getattr(config, "FLYER_TAGLINE_TEXT", "—  Te esperamos en Fiore  —")
    if tagline:
        _draw_tagline(img, tagline, y + int(H * 0.014))

    footer = getattr(config, "FLYER_FOOTER_TEXT", "Hecho en casa, todos los días")
    if footer:
        _draw_footer_pill(img, footer)

    out = io.BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=92)
    return out.getvalue()
