"""
make_cutout.py — kisi bhi player ka transparent CUTOUT bana ke
remotion-footy/public/cut/<slug>.png me daal deta he.

Isse hi asli variety aati he: live data me jo bhi naam aaye (Bellingham, Kane,
Dembele...) uska cutout khud ban jaata he, to har din naye chehre use ho sakte he.

Source: Wikidata P18 / Wikimedia Commons (realphoto.py) — free + attribution-safe.
Background: rembg (local, offline).

Chalao:
    python make_cutout.py "Jude Bellingham"
    python make_cutout.py "Harry Kane" "Ousmane Dembele"
"""

import io
import os
import re
import sys
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
CUT_DIR = os.path.join(ROOT, "remotion-footy", "public", "cut")
CREDITS = os.path.join(ROOT, "data", "cutout_credits.json")

MIN_PX = 220          # isse chhoti cutout 1080x1920 pe dhundhli lagegi


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "", name.lower().split()[-1])
    return s or re.sub(r"[^a-z0-9]+", "", name.lower())


def _credits() -> dict:
    if os.path.exists(CREDITS):
        with open(CREDITS, encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def make(name: str, force: bool = False) -> str | None:
    """Player ka cutout banao. Lauta hua path, ya None agar fail."""
    from PIL import Image
    import realphoto
    from rembg import remove

    key = slug(name)
    out = os.path.join(CUT_DIR, f"{key}.png")
    if os.path.exists(out) and not force:
        print(f"[skip] {key}.png pehle se he")
        return out

    img, credit, fn = realphoto.real_photo(name, sentence=f"{name} footballer portrait")
    if img is None:
        print(f"[fail] {name}: koi photo nahi mili")
        return None

    cut = remove(img)                       # RGBA
    bbox = cut.getbbox()                    # transparent border trim
    if bbox:
        cut = cut.crop(bbox)

    if cut.width < MIN_PX or cut.height < MIN_PX:
        print(f"[fail] {name}: cutout bahut chhota ({cut.width}x{cut.height})")
        return None

    # Alpha ka kitna hissa bacha — 2% se kam matlab rembg ne sab kuch kaat diya
    alpha = cut.getchannel("A")
    filled = sum(alpha.histogram()[200:]) / float(cut.width * cut.height)
    if filled < 0.02:
        print(f"[fail] {name}: rembg ne poora subject kaat diya ({filled:.1%})")
        return None

    os.makedirs(CUT_DIR, exist_ok=True)
    cut.save(out)

    cr = _credits()
    cr[key] = {"name": name, "credit": credit, "file": fn}
    os.makedirs(os.path.dirname(CREDITS), exist_ok=True)
    with open(CREDITS, "w", encoding="utf-8") as f:
        json.dump(cr, f, ensure_ascii=False, indent=2)

    print(f"[ok] {key}.png  {cut.width}x{cut.height}  filled={filled:.0%}  ({credit})")
    return out


def have(name: str) -> bool:
    return os.path.exists(os.path.join(CUT_DIR, f"{slug(name)}.png"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
    for n in sys.argv[1:]:
        make(n)
