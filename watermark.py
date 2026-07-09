"""
Diseño de flyer estilo "póster" para Sandwichería FIORE Confitería (v3).

Igual que la v2 (logo grande, titular Anton sobre cintas inclinadas, acento
manuscrito, píldora "Hecho en casa") pero con COLOCACIÓN INTELIGENTE:
antes de ubicar el texto y el logo, se calcula un mapa de detalle visual de
la foto (bordes + contraste = producto) y cada elemento se coloca en la zona
candidata con MENOS producto debajo, para no taparlo.

Funciones usadas por main.py: apply_full_design(), slot_suffix(),
extract_slot_from_filename(), slots_for_filename().
"""

import io
import zlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

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
    "desayuno": {"c1": DORADO, "t1": OSCURO, "c2": CREMA, "t2": ROJO,   "c3": VERDE,  "t3": BLANCO},
    "almuerzo": {"c1": ROJO,   "t1": BLANCO, "c2": CREMA, "t2": ROJO,   "c3": OSCURO, "t3": DORADO},
    "merienda": {"c1": VERDE,  "t1": BLANCO, "c2": CREMA, "t2": VERDE,  "c3": ROJO,   "t3": BLANCO},
    "cena":     {"c1": OSCURO, "t1": DORADO, "c2": CREMA, "t2": OSCURO, "c3": ROJO,   "t3": BLANCO},
}

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
# Mapa de detalle: dónde está el producto
# ------------------------------------------------------------------

def _detail_map(img):
    """Mapa chico (ancho 200) de dónde está el producto. Combina tres señales:
    - qué tan distinto es cada pixel del color del fondo (estimado en los bordes
      de la foto): el producto suele despegarse del fondo aunque sea liso;
    - bordes/textura (detalle en foco);
    - cercanía al centro (el producto suele estar centrado).
    Zonas claras = producto; zonas oscuras = lugar seguro para el texto."""
    from PIL import ImageChops, ImageOps

    w = 200
    h = max(1, int(img.height * w / img.width))
    small = img.convert("RGB").resize((w, h), Image.BILINEAR)

    # color de fondo: mediana de los marcos superior e inferior de la foto
    edge_px = max(2, h // 10)
    top = ImageStat.Stat(small.crop((0, 0, w, edge_px))).median
    bottom = ImageStat.Stat(small.crop((0, h - edge_px, w, h))).median
    bg = tuple((a + b) // 2 for a, b in zip(top, bottom))
    distinct = ImageChops.difference(small, Image.new("RGB", small.size, bg)).convert("L")
    distinct = ImageOps.autocontrast(distinct, cutoff=2)

    edges = small.convert("L").filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.autocontrast(edges, cutoff=2)

    center = ImageOps.invert(Image.radial_gradient("L")).resize(small.size, Image.BILINEAR)

    sal = Image.blend(distinct, edges, 0.35)     # 65% color distinto, 35% bordes
    sal = Image.blend(sal, center, 0.18)         # + un poco de prior central
    return sal.filter(ImageFilter.GaussianBlur(4))


def _region_detail(dmap, base_size, box):
    """Detalle promedio (0-255) de un rectángulo de la imagen original."""
    W, H = base_size
    sx, sy = dmap.width / W, dmap.height / H
    x0 = max(0, int(box[0] * sx)); y0 = max(0, int(box[1] * sy))
    x1 = min(dmap.width, int(box[2] * sx)); y1 = min(dmap.height, int(box[3] * sy))
    if x1 <= x0 or y1 <= y0:
        return 255.0
    return ImageStat.Stat(dmap.crop((x0, y0, x1, y1))).mean[0]


def _best_position(dmap, base_size, layer_size, candidates, bias=None):
    """Elige la posición (x, y) cuyo rectángulo tape menos detalle.
    bias: dict {indice: descuento} para preferir posiciones clásicas en empates."""
    best, best_score = candidates[0], None
    for i, (x, y) in enumerate(candidates):
        box = (x, y, x + layer_size[0], y + layer_size[1])
        score = _region_detail(dmap, base_size, box)
        if bias and i in bias:
            score -= bias[i]
        if best_score is None or score < best_score:
            best, best_score = (x, y), score
    return best


# ------------------------------------------------------------------
# Recorte al formato del feed de Instagram (4:5)
# ------------------------------------------------------------------

# Instagram solo acepta fotos de feed entre 4:5 (vertical) y 1.91:1 (apaisada).
# Las fotos de celular (3:4, 9:16) son más verticales que 4:5 y la API las
# rechaza con error 400, así que se recortan a 4:5 conservando el producto.
_FEED_RATIO_MIN = 4 / 5      # ancho/alto mínimo (vertical máxima)
_FEED_RATIO_MAX = 1.91       # ancho/alto máximo (apaisada máxima)
_FEED_MAX_WIDTH = 1440       # ancho máximo recomendado por Meta


def _crop_to_feed(img):
    """Recorta la imagen al rango de proporciones válido para el feed,
    eligiendo la ventana de recorte que más producto conserva (según el
    mapa de saliencia). Después limita el ancho a 1440px."""
    W, H = img.size
    ratio = W / H

    if ratio < _FEED_RATIO_MIN:            # demasiado vertical: recortar alto
        new_h = int(W / _FEED_RATIO_MIN)
        dmap = _detail_map(img)
        best_y, best_score = 0, -1.0
        for frac in (0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0):
            y = int((H - new_h) * frac)
            score = _region_detail(dmap, (W, H), (0, y, W, y + new_h))
            if score > best_score:          # acá se busca MÁXIMO detalle adentro
                best_y, best_score = y, score
        img = img.crop((0, best_y, W, best_y + new_h))
    elif ratio > _FEED_RATIO_MAX:          # demasiado apaisada: recortar ancho
        new_w = int(H * _FEED_RATIO_MAX)
        dmap = _detail_map(img)
        best_x, best_score = 0, -1.0
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            x = int((W - new_w) * frac)
            score = _region_detail(dmap, (W, H), (x, 0, x + new_w, H))
            if score > best_score:
                best_x, best_score = x, score
        img = img.crop((best_x, 0, best_x + new_w, H))

    if img.width > _FEED_MAX_WIDTH:
        img = img.resize((_FEED_MAX_WIDTH, int(img.height * _FEED_MAX_WIDTH / img.width)), Image.LANCZOS)
    return img


# ------------------------------------------------------------------
# Piezas del diseño
# ------------------------------------------------------------------

def _ref(base):
    W, H = base.size
    return min(W, int(H * 0.8))


def _build_logo(ref):
    """Logo con sombra sobre lienzo transparente (para pegar donde convenga)."""
    logo = Image.open(config.LOGO_PATH).convert("RGBA")
    target_w = int(ref * getattr(config, "FLYER_LOGO_WIDTH_RATIO_V2", 0.38))
    ratio = target_w / logo.width
    logo = logo.resize((target_w, int(logo.height * ratio)), Image.LANCZOS)

    alpha = logo.split()[3]
    shadow = Image.new("RGBA", logo.size, (0, 0, 0, 0))
    shadow.putalpha(alpha.point(lambda a: int(a * 0.55)))
    blur = max(3, int(ref * 0.010))
    canvas = Image.new("RGBA", (logo.width + blur * 6, logo.height + blur * 6), (0, 0, 0, 0))
    canvas.alpha_composite(shadow, (blur * 3 + int(ref * 0.006), blur * 3 + int(ref * 0.010)))
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(logo, (blur * 3, blur * 3))
    return canvas


def _ribbon_layer(text, font, ref, bg, fg, angle=-2.5, pad_x_ratio=0.55, pad_y_ratio=0.30):
    """Cinta de color inclinada con sombra dura, sobre lienzo transparente."""
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = int(th * pad_x_ratio), int(th * pad_y_ratio)
    w, h = tw + pad_x * 2, th + pad_y * 2
    off = max(3, int(ref * 0.008))

    layer = Image.new("RGBA", (w + off * 3, h + off * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = max(2, int(h * 0.10))
    d.rounded_rectangle([off, off, off + w, off + h], radius=r, fill=(15, 15, 17, 200))
    d.rounded_rectangle([0, 0, w, h], radius=r, fill=bg)
    d.text((pad_x - bbox[0], pad_y - bbox[1]), text, font=font, fill=fg)

    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    return layer


def _script_layer(text, ref, max_width):
    """Línea manuscrita (Pacifico) con sombra, sobre lienzo transparente."""
    font = _fit_font(_SCRIPT_FONT_PATH, text, max_width, int(ref * 0.055))
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
    return layer


def _split_headline(text, font_path, max_width, size):
    font = _load_font(font_path, size)
    bbox = font.getbbox(text)
    if bbox[2] - bbox[0] <= max_width:
        return [text]
    words = text.split()
    if len(words) < 2:
        return [text]
    best, best_diff = 1, None
    for i in range(1, len(words)):
        diff = abs(len(" ".join(words[:i])) - len(" ".join(words[i:])))
        if best_diff is None or diff < best_diff:
            best, best_diff = i, diff
    return [" ".join(words[:best]), " ".join(words[best:])]


def _build_text_block(base, theme, headline, subtitle, accent, scale=1.0):
    """Arma el bloque completo (cintas + acento manuscrito) sobre un lienzo
    transparente, para poder medirlo y ubicarlo donde menos tape.
    scale < 1 genera un bloque más compacto (para fotos llenas de producto)."""
    W, H = base.size
    ref = int(_ref(base) * scale)
    max_w = int(W * 0.80 * max(scale, 0.85))

    head_size = int(ref * 0.095)
    lines = _split_headline(headline.upper(), _HEADLINE_FONT_PATH, max_w - int(head_size * 1.1), head_size)

    layers, y, x_off = [], 0, 0
    for i, line in enumerate(lines):
        font = _fit_font(_HEADLINE_FONT_PATH, line, max_w - int(head_size * 1.1), head_size)
        bg, fg = (theme["c1"], theme["t1"]) if i % 2 == 0 else (theme["c2"], theme["t2"])
        lay = _ribbon_layer(line, font, ref, bg, fg)
        layers.append((lay, x_off, y))
        y += int(lay.height * 0.82)
        x_off += int(ref * 0.030)

    sub_font = _fit_font(_SANS_FONT_PATH, subtitle.upper(), int(max_w * 0.9), int(ref * 0.035))
    lay = _ribbon_layer(subtitle.upper(), sub_font, ref, theme["c3"], theme["t3"],
                        pad_x_ratio=0.75, pad_y_ratio=0.45)
    layers.append((lay, int(ref * 0.015), y + int(ref * 0.006)))
    y += int(lay.height * 0.95) + int(ref * 0.014)

    if accent:
        lay = _script_layer(accent, ref, int(W * 0.6))
        layers.append((lay, int(ref * 0.05), y))
        y += lay.height

    block_w = max(x + lay.width for lay, x, _ in layers)
    block = Image.new("RGBA", (block_w, y + int(ref * 0.01)), (0, 0, 0, 0))
    for lay, x, yy in layers:
        block.alpha_composite(lay, (x, yy))
    return block


def _draw_heart(draw, cx, cy, size, color):
    r = size / 4
    draw.ellipse([cx - 2 * r, cy - 2 * r, cx, cy], fill=color)
    draw.ellipse([cx, cy - 2 * r, cx + 2 * r, cy], fill=color)
    draw.polygon([(cx - 2 * r, cy - r * 0.6), (cx + 2 * r, cy - r * 0.6), (cx, cy + 2 * r)], fill=color)


def _draw_footer_pill(base, text):
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
# Diseño completo con colocación inteligente
# ------------------------------------------------------------------

def apply_full_design(image_bytes, slot, seed_name=""):
    """
    Aplica el diseño estilo póster sobre la foto original, ubicando el logo y
    el bloque de texto donde MENOS tapen el producto, y devuelve bytes JPEG.
    """
    slot = slot or "almuerzo"
    theme = _SLOT_THEME.get(slot, _SLOT_THEME["almuerzo"])
    headline, subtitle = _pick_phrase(slot, seed_name)

    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    img = _crop_to_feed(img)   # asegurar proporción válida para Instagram
    W, H = img.size
    ref = _ref(img)
    dmap = _detail_map(img)
    margin = int(ref * 0.045)

    # --- logo: arriba, en la posición horizontal con menos producto ---
    logo = _build_logo(ref)
    y_logo = int(ref * 0.02)
    logo_candidates = [
        ((W - logo.width) // 2, y_logo),          # centro (clásico)
        (margin, y_logo),                          # izquierda
        (W - logo.width - margin, y_logo),         # derecha
    ]
    lx, ly = _best_position(dmap, (W, H), logo.size, logo_candidates, bias={0: 8})
    img.alpha_composite(logo, (lx, ly))
    logo_bottom = ly + logo.height - int(ref * 0.03)

    # --- bloque de texto: la combinación (altura x lado) que menos tape.
    # Si toda la foto está ocupada por producto, se prueba con un bloque más
    # chico (85% y 72%) hasta que lo tapado sea aceptable. ---
    accent = getattr(config, "FLYER_ACCENT_TEXT", "Lomas de Zamora")
    footer_space = int(H * 0.115)
    best_overall = None

    for scale in (1.0, 0.85, 0.72):
        block = _build_text_block(img, theme, headline, subtitle, accent, scale=scale)
        x_left = int(W * 0.055)
        x_right = max(x_left, W - block.width - int(W * 0.055))

        ys = [logo_bottom + int(ref * 0.030)]                   # bajo el logo (clásico)
        y_mid = int(H * 0.42)
        y_low = H - footer_space - block.height
        if y_mid > ys[0] + int(ref * 0.05) and y_mid + block.height < y_low:
            ys.append(y_mid)
        if y_low > ys[0] + int(ref * 0.05):
            ys.append(y_low)

        for i, y in enumerate(ys):
            for x in {x_left, x_right}:
                box = (x, y, x + block.width, y + block.height)
                score = _region_detail(dmap, (W, H), box)
                if i == 0 and x == x_left:
                    score -= 6      # leve preferencia por el layout clásico
                score += (1.0 - scale) * 20  # preferir el tamaño grande si empatan
                if best_overall is None or score < best_overall[0]:
                    best_overall = (score, block, x, y)

        # si ya hay una posición que casi no tapa producto, no achicar más
        if best_overall and best_overall[0] <= 95:
            break

    _, block, bx, by = best_overall
    img.alpha_composite(block, (bx, by))

    footer = getattr(config, "FLYER_FOOTER_TEXT", "Hecho en casa, todos los días")
    if footer:
        _draw_footer_pill(img, footer)

    out = io.BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=92)
    return out.getvalue()
