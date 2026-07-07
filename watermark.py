"""
Aplica la marca de agua (texto o logo) a una imagen usando Pillow.
"""

import io
from PIL import Image, ImageDraw, ImageFont

import config

# Rutas de respaldo si la fuente configurada no se encuentra (evita caer en la
# fuente de emergencia de Pillow, que es diminuta e ilegible).
_FALLBACK_FONT_PATHS = [
    "assets/fonts/Poppins-Bold.ttf",
    "assets/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(preferred_path, size):
    """Intenta cargar la fuente preferida; si falla, prueba rutas de respaldo conocidas."""
    candidates = [preferred_path] + [p for p in _FALLBACK_FONT_PATHS if p != preferred_path]
    for path in candidates:
        try:
            font = ImageFont.truetype(path, size)
            if path != preferred_path:
                print(f"[watermark] Aviso: no se encontró '{preferred_path}', usando '{path}' en su lugar.")
            return font
        except OSError:
            continue
    print(f"[watermark] Aviso: ninguna fuente .ttf encontrada, usando la fuente de emergencia de Pillow (chica).")
    return ImageFont.load_default()


def _get_position(img_w, img_h, elem_w, elem_h, position, margin):
    positions = {
        "bottom-right": (img_w - elem_w - margin, img_h - elem_h - margin),
        "bottom-left": (margin, img_h - elem_h - margin),
        "top-right": (img_w - elem_w - margin, margin),
        "top-left": (margin, margin),
        "center": ((img_w - elem_w) // 2, (img_h - elem_h) // 2),
    }
    return positions.get(position, positions["bottom-right"])


def _apply_text_watermark(base_img):
    draw_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(draw_layer)

    font_size = max(int(base_img.width * config.FONT_SIZE_RATIO), 12)
    try:
        font = ImageFont.truetype(config.FONT_PATH, font_size)
    except OSError:
        font = ImageFont.load_default()

    text = config.BUSINESS_NAME
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=config.TEXT_STROKE_WIDTH)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    pad = config.TEXT_BACKGROUND_PADDING
    x, y = _get_position(
        base_img.width, base_img.height,
        text_w + pad * 2, text_h + pad * 2,
        config.WATERMARK_POSITION, config.WATERMARK_MARGIN,
    )

    if config.TEXT_BACKGROUND_COLOR:
        draw.rounded_rectangle(
            [x, y, x + text_w + pad * 2, y + text_h + pad * 2],
            radius=10,
            fill=config.TEXT_BACKGROUND_COLOR,
        )

    draw.text(
        (x + pad - bbox[0], y + pad - bbox[1]),
        text,
        font=font,
        fill=config.TEXT_COLOR,
        stroke_width=config.TEXT_STROKE_WIDTH,
        stroke_fill=config.TEXT_STROKE_COLOR,
    )

    return Image.alpha_composite(base_img, draw_layer)


def _apply_logo_watermark(base_img):
    logo = Image.open(config.LOGO_PATH).convert("RGBA")

    target_w = int(base_img.width * config.LOGO_WIDTH_RATIO)
    ratio = target_w /
