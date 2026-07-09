"""
thumbnail.py — YouTube ke liye 16:9 thumbnail (1280x720) banata hai.

Best image (hook) leta hai, 16:9 me crop karta hai, dark gradient + bada bold
title text (Hindi support ke saath) aur brand name lagata hai.
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import config


# Hindi (Devanagari) + English dono ke liye font — Windows par Nirmala UI (.ttc)
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/Nirmala.ttc",    # Nirmala UI (Devanagari + Latin)
    "C:/Windows/Fonts/mangal.ttf",     # Mangal (Devanagari)
    "C:/Windows/Fonts/Aparajita.ttf",
    # Linux (GitHub Actions) — Devanagari (Hindi title) ke liye
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
    "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
    "C:/Windows/Fonts/arialbd.ttf",    # last resort (Latin only)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _font(size: int):
    for f in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _line_w(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def _fit(draw, text, max_w, start, min_size=44):
    size = start
    while size >= min_size:
        font = _font(size)
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = f"{cur} {w}".strip()
            if _line_w(draw, t, font) <= max_w or not cur:
                cur = t
            else:
                lines.append(cur); cur = w
        if cur:
            lines.append(cur)
        if all(_line_w(draw, ln, font) <= max_w for ln in lines):
            return lines, font, size
        size -= 4
    return lines, _font(min_size), min_size


def _cover(img, w, h):
    img = img.convert("RGB")
    sw, sh = img.size
    scale = max(w / sw, h / sh)
    img = img.resize((int(sw * scale) + 1, int(sh * scale) + 1), Image.LANCZOS)
    nw, nh = img.size
    return img.crop(((nw - w) // 2, (nh - h) // 2,
                     (nw - w) // 2 + w, (nh - h) // 2 + h))


def _first_base(media):
    """media (dicts ya strings) se pehli usable image; na mile to video frame."""
    items = [{"type": "image", "path": m} if isinstance(m, str) else m
             for m in media]
    for it in items:
        if it.get("type") == "image":
            try:
                return Image.open(it["path"])
            except Exception:
                pass
    for it in items:
        if it.get("type") == "video":
            try:
                import imageio.v2 as iio
                rdr = iio.get_reader(it["path"])
                frame = rdr.get_data(15)
                rdr.close()
                return Image.fromarray(frame)
            except Exception:
                pass
    return None


def make_thumbnail(data: dict, media: list, out_path: str = None) -> str:
    W, H = config.THUMB_WIDTH, config.THUMB_HEIGHT
    out_path = out_path or os.path.join(config.OUTPUT_DIR, "thumbnail.jpg")

    base = _first_base(media)
    base = _cover(base, W, H) if base else Image.new("RGB", (W, H), (12, 24, 48))

    # Dark gradient bottom (text readability)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(H):
        a = int(200 * (y / H) ** 1.4)
        od.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    base = Image.alpha_composite(base.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(base)

    # Title (bada, neeche)
    title = data.get("youtube_title") or data.get("title_hindi") or "Football Short"
    # emoji thumbnail font me render nahi hote — hata dete hain
    title = "".join(ch for ch in title if ord(ch) < 0x2190).strip()
    lines, font, size = _fit(draw, title.upper(), W - 120, 96)

    line_h = size + 16
    y = H - line_h * len(lines) - 70
    for ln in lines:
        x = 60
        for dx in (-4, 0, 4):
            for dy in (-4, 0, 4):
                draw.text((x + dx, y + dy), ln, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), ln, font=font, fill=(255, 222, 60, 255))
        y += line_h

    # Brand name — top-left chip
    brand = config.BRAND_NAME or config.BRAND_HANDLE
    if brand:
        bf = _font(40)
        bw = _line_w(draw, brand, bf)
        draw.rectangle([40, 36, 40 + bw + 36, 36 + 60], fill=(220, 30, 40, 235))
        draw.text((58, 46), brand, font=bf, fill=(255, 255, 255, 255))

    base.convert("RGB").save(out_path, quality=90)
    print(f"[thumb] saved {out_path}")
    return out_path
