"""
Aplica la marca de agua (texto o logo) a una imagen usando Pillow.
"""

import io
from PIL import Image, ImageDraw, ImageFont

import config


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
    ratio = target_w / logo.width
    target_h = int(logo.height * ratio)
    logo = logo.resize((target_w, target_h), Image.LANCZOS)

    if config.LOGO_OPACITY < 1.0:
        alpha = logo.split()[3].point(lambda p: int(p * config.LOGO_OPACITY))
        logo.putalpha(alpha)

    pad = config.LOGO_BACKGROUND_PADDING if config.LOGO_BACKGROUND_COLOR else 0
    x, y = _get_position(
        base_img.width, base_img.height,
        target_w + pad * 2, target_h + pad * 2,
        config.WATERMARK_POSITION, config.WATERMARK_MARGIN,
    )

    layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    if config.LOGO_BACKGROUND_COLOR:
        draw.rounded_rectangle(
            [x, y, x + target_w + pad * 2, y + target_h + pad * 2],
            radius=config.LOGO_BACKGROUND_RADIUS,
            fill=config.LOGO_BACKGROUND_COLOR,
        )

    layer.paste(logo, (x + pad, y + pad), logo)
    return Image.alpha_composite(base_img, layer)


def apply_watermark(image_bytes, output_format="JPEG"):
    """
    Recibe los bytes de una imagen, le aplica la marca de agua configurada,
    y devuelve los bytes resultantes (JPEG por defecto).
    """
    base_img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    if config.WATERMARK_MODE == "logo":
        result = _apply_logo_watermark(base_img)
    else:
        result = _apply_text_watermark(base_img)

    if output_format.upper() == "JPEG":
        result = result.convert("RGB")

    out_buffer = io.BytesIO()
    result.save(out_buffer, format=output_format, quality=92)
    return out_buffer.getvalue()


def apply_flyer_banner(image_bytes, slot, output_format="JPEG"):
    """
    Agrega un banner inferior tipo flyer con el estilo y texto de la franja
    horaria (desayuno/almuerzo/merienda/cena). Se aplica sobre una imagen que
    ya puede tener el logo (de 'editadas'). No modifica el archivo en Drive:
    se usa solo para la versión que se publica en Instagram.
    """
    if not config.FLYER_BANNER_ENABLED or slot not in config.SLOT_STYLES:
        # Sin estilo definido para esta franja: devolver la imagen sin cambios
        img = Image.open(io.BytesIO(image_bytes))
        if output_format.upper() == "JPEG":
            img = img.convert("RGB")
        out = io.BytesIO()
        img.save(out, format=output_format, quality=92)
        return out.getvalue()

    style = config.SLOT_STYLES[slot]
    base_img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = base_img.size

    banner_h = int(h * config.FLYER_BANNER_HEIGHT_RATIO)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    # Franja de color, pegada al borde inferior
    draw.rectangle([0, h - banner_h, w, h], fill=style["bg_color"])

    # Línea delgada de acento arriba de la franja (detalle prolijo, como en tus flyers)
    accent_h = max(int(banner_h * 0.04), 3)
    draw.rectangle([0, h - banner_h - accent_h, w, h - banner_h], fill=style["text_color"])

    # Título (headline)
    try:
        headline_font_size = max(int(w * 0.075), 20)
        headline_font = ImageFont.truetype(config.FLYER_HEADLINE_FONT_PATH, headline_font_size)
    except OSError:
        headline_font = ImageFont.load_default()

    headline = style["headline"]
    bbox = draw.textbbox((0, 0), headline, font=headline_font)
    text_w = bbox[2] - bbox[0]
    while text_w > w * 0.92 and headline_font_size > 14:
        headline_font_size -= 2
        headline_font = ImageFont.truetype(config.FLYER_HEADLINE_FONT_PATH, headline_font_size)
        bbox = draw.textbbox((0, 0), headline, font=headline_font)
        text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    headline_y = h - banner_h + int(banner_h * 0.16) - bbox[1]
    draw.text(((w - text_w) // 2, headline_y), headline, font=headline_font, fill=style["text_color"])

    # Subtítulo (nombre del negocio + ubicación)
    try:
        subtitle_font_size = max(int(w * 0.032), 12)
        subtitle_font = ImageFont.truetype(config.FLYER_SUBTITLE_FONT_PATH, subtitle_font_size)
    except OSError:
        subtitle_font = ImageFont.load_default()

    subtitle = config.FLYER_SUBTITLE_TEXT
    sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    subtitle_y = headline_y + text_h + int(banner_h * 0.14)
    draw.text(((w - sub_w) // 2, subtitle_y), subtitle, font=subtitle_font, fill=style["text_color"])

    result = Image.alpha_composite(base_img, layer)

    if output_format.upper() == "JPEG":
        result = result.convert("RGB")

    out_buffer = io.BytesIO()
    result.save(out_buffer, format=output_format, quality=92)
    return out_buffer.getvalue()
