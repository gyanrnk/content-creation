"""
media.py — Har segment ke liye image laata hai aur 9:16 (1080x1920) me crop karta hai.

Sources:
  - REAL  : Wikimedia Commons (free, no key) ya Pexels (PEXELS_API_KEY ho to)
            → real players, teams, stadiums, trophy ke liye.
  - AI    : Pollinations (free FLUX, no GPU, no key)
            → generic atmospheric visuals ke liye.

Agar real image na mile to automatically AI fallback ho jaata hai (kabhi blank
frame nahi aayega).
"""

import os
import io
import re
import glob
import random
import collections
import urllib.parse
import requests
from PIL import Image, ImageEnhance
from dotenv import load_dotenv

import config

# stat segment detect (number + stat-word) — stat card ke background ke liye
_STAT_RE = re.compile(r"\d[\d,]{0,9}\s+(cup|cups|goal|goals|match|matches|trophy|"
                      r"trophies|title|titles|year|years|cap|caps|win|wins|record|"
                      r"final|finals|medal|medals|assist|assists)", re.I)
_MAIN_NAMES = ["messi", "ronaldo", "neymar", "mbappe", "pele", "maradona", "modric",
               "benzema", "haaland", "ramos", "brazil", "argentina", "portugal",
               "france", "spain", "germany", "england", "italy", "japan", "morocco"]


def _main_subject(segments) -> str:
    """Video ka dominant PLAYER (ya na mile to team).

    BUG jo fix hua: pehle ek chhoti hardcoded list (_MAIN_NAMES, jyadatar team naam)
    thi — Leao/Kane/Baggio usme the hi nahi, to "Rafael Leao" wali video "Portugal"
    pakad leti thi (Leao Portugal ka hai) aur har video me wahi TEAM GROUP PHOTO
    aa jaati thi. Ab: poora ideas.PLAYERS pool + PLAYER ko TEAM se pehle priority.
    """
    text = " ".join(((s.get("image_query") or "") + " " +
                     (s.get("subtitle_english") or "")).lower() for s in segments)
    try:
        from ideas import PLAYERS, TEAMS
    except Exception:
        PLAYERS, TEAMS = [], []

    def _best(names):
        cnt = collections.Counter()
        for nm in names:
            n = nm.lower()
            c = text.count(n)
            last = n.split()[-1]
            if len(last) > 4 and last != n:      # "Leao" bhi ginon, "Rafael Leao" bhi
                c += text.count(last)
            if c:
                cnt[nm] = c
        return cnt.most_common(1)[0][0] if cnt else None

    # 1) asli PLAYER dhoondo (yahi chehra chahiye)
    p = _best(PLAYERS)
    if p:
        return p
    # 2) warna team (group photo — sirf jab koi player named na ho)
    t = _best(TEAMS)
    if t:
        return t
    # 3) purani chhoti list = last resort
    cnt = collections.Counter()
    for nm in _MAIN_NAMES:
        c = text.count(nm)
        if c:
            cnt[nm] = c
    return cnt.most_common(1)[0][0].title() if cnt else None

load_dotenv()

_HEADERS = {"User-Agent": "WC2026-Shorts/1.0 (content generator)"}


# ── Local media LIBRARY (tumhare collect kiye free clips/images) ─────────────────
def _library_files() -> list[str]:
    """assets/library/ me jo bhi images/videos daaloge, unme se random pick honge."""
    if not getattr(config, "USE_LIBRARY", False):
        return []
    d = getattr(config, "LIBRARY_DIR", "assets/library")
    if not os.path.isdir(d):
        return []
    files = []
    for ext in ("*.mp4", "*.mov", "*.webm", "*.jpg", "*.jpeg", "*.png", "*.webp"):
        files += glob.glob(os.path.join(d, ext))
        files += glob.glob(os.path.join(d, ext.upper()))
    return files


_VID_EXT = (".mp4", ".mov", ".webm")


# ── Helpers ─────────────────────────────────────────────────────────────────────
def _cover_crop(img: Image.Image, w: int, h: int) -> Image.Image:
    """Image ko 9:16 me 'cover' style fit karta hai (no stretch, center crop)."""
    img = img.convert("RGB")
    src_w, src_h = img.size
    scale = max(w / src_w, h / src_h)
    new = img.resize((int(src_w * scale) + 1, int(src_h * scale) + 1),
                     Image.LANCZOS)
    nw, nh = new.size
    left = (nw - w) // 2
    top = (nh - h) // 2
    return new.crop((left, top, left + w, top + h))


def _grade(img: Image.Image) -> Image.Image:
    """Cinematic color grade — contrast + saturation + halka warm tint."""
    if not config.CINEMATIC_GRADE:
        return img
    img = img.convert("RGB")
    img = ImageEnhance.Contrast(img).enhance(1.18)
    img = ImageEnhance.Color(img).enhance(1.28)
    img = ImageEnhance.Brightness(img).enhance(0.97)
    # Halka teal-orange: warm highlights (red boost), cool shadows (blue boost)
    r, g, b = img.split()
    r = r.point(lambda v: min(255, int(v * 1.06)))
    b = b.point(lambda v: min(255, int(v * 1.04)))
    return Image.merge("RGB", (r, g, b))


def _save(img: Image.Image, idx: int) -> str:
    out_dir = os.path.join(config.OUTPUT_DIR, "images")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"img_{idx:02d}.jpg")
    img.save(path, quality=90)
    return path


# ── Real image: Wikimedia Commons ────────────────────────────────────────────────
def _wikimedia(query: str):
    try:
        r = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query", "format": "json",
                "generator": "search", "gsrsearch": query,
                "gsrnamespace": 6, "gsrlimit": 5,
                "prop": "imageinfo", "iiprop": "url|mime",
                "iiurlwidth": 1200,
            },
            headers=_HEADERS, timeout=30,
        )
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        for p in pages.values():
            info = p.get("imageinfo", [{}])[0]
            mime = info.get("mime", "")
            url = info.get("thumburl") or info.get("url")
            if url and mime.startswith("image") and "svg" not in mime:
                img_r = requests.get(url, headers=_HEADERS, timeout=30)
                img_r.raise_for_status()
                return Image.open(io.BytesIO(img_r.content))
    except Exception as e:
        print(f"[media] Wikimedia failed for {query!r}: {e}")
    return None


# ── Real image: Openverse (free, no key — best for real players/football) ────────
def _openverse(query: str):
    try:
        r = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": query, "page_size": 8, "license_type": "all",
                    "mature": "false"},
            headers=_HEADERS, timeout=30,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        random.shuffle(results)   # random result = repeat nahi hota
        for x in results:
            url = x.get("url")
            # API metadata se hi chhoti images skip karo
            if not url or (x.get("width") or 0) < 640 or (x.get("height") or 0) < 640:
                continue
            try:
                ir = requests.get(url, headers=_HEADERS, timeout=30)
                if ir.status_code != 200 or len(ir.content) < 8000:
                    continue
                img = Image.open(io.BytesIO(ir.content))
                # download ke baad bhi low-res junk filter
                if img.width >= 600 and img.height >= 600:
                    return img
            except Exception:
                continue
    except Exception as e:
        print(f"[media] Openverse failed for {query!r}: {e}")
    return None


# Atmospheric segments ke liye real football B-roll queries (rotate by index)
# Bada pool = kam repeat (user: "same free clip baar-baar aata hai"). 96+ clip-ids
# already use ho chuke the aur pool sirf 8 query ka tha -> wahi clips ghoom rahe the.
_BROLL = [
    "football stadium crowd", "soccer ball on grass", "football match action",
    "stadium floodlights night", "football fans celebration",
    "soccer player running", "football pitch aerial", "trophy celebration",
    "soccer goal net close up", "football boots close up", "soccer dribbling skills",
    "goalkeeper diving save", "corner kick stadium", "football tactics board",
    "soccer training session", "packed stadium tifo", "referee whistle match",
    "soccer ball slow motion", "night match stadium lights", "football crowd chanting",
    "empty football stadium", "soccer penalty kick", "football team huddle",
    "green grass pitch closeup", "stadium seats sunset", "soccer ball spinning",
]


# ── Real image: Pexels (optional) ────────────────────────────────────────────────
def _pexels(query: str):
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": 1, "orientation": "portrait"},
            timeout=30,
        )
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if photos:
            url = photos[0]["src"]["large2x"]
            img_r = requests.get(url, timeout=30)
            return Image.open(io.BytesIO(img_r.content))
    except Exception as e:
        print(f"[media] Pexels failed for {query!r}: {e}")
    return None


# ── AI image: Pollinations (free FLUX) ───────────────────────────────────────────
def _pollinations(prompt: str, seed: int = None, tries: int = 4):
    import time
    # RANDOM seed = har video me alag image (repeat nahi hoti)
    if seed is None:
        seed = random.randint(1, 9_999_999)
    enc = urllib.parse.quote(prompt)
    url = (f"https://image.pollinations.ai/prompt/{enc}"
           f"?width={config.WIDTH}&height={config.HEIGHT}"
           f"&model={config.AI_IMAGE_MODEL}&nologo=true&seed={seed}")
    for i in range(tries):
        try:
            r = requests.get(url, headers=_HEADERS, timeout=150)
            if r.status_code == 200 and len(r.content) > 1000:
                return Image.open(io.BytesIO(r.content))
            print(f"[media]   Pollinations busy (HTTP {r.status_code}), "
                  f"retry in {6 * (i + 1)}s...")
        except Exception as e:
            print(f"[media]   Pollinations error ({e}), retry...")
        time.sleep(6 * (i + 1))
    return None


# ── Real video clip: Pexels (free key) ───────────────────────────────────────────
def _pexels_video(query: str, idx: int, exclude=None):
    """Vertical football clip download. Returns (mp4_path, video_id) ya (None, None)."""
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return None, None
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": 5, "orientation": "portrait",
                    "size": "medium"},
            timeout=30,
        )
        r.raise_for_status()
        vids = r.json().get("videos", [])
        random.shuffle(vids)   # random video = repeat nahi
        target = getattr(config, "PEXELS_MAX_HEIGHT", 1280)
        # pehle un videos ko try karo jo pehle use nahi hue (cross-video variety)
        exclude = exclude or set()
        vids = [v for v in vids if str(v.get("id")) not in exclude] + \
               [v for v in vids if str(v.get("id")) in exclude]
        for v in vids:
            cands = [f for f in v.get("video_files", [])
                     if f.get("link") and (f.get("height") or 0) >= 700]
            if not cands:
                continue
            # target (1280) tak ki sabse achhi res -> chhoti file, fast render
            under = [f for f in cands if (f.get("height") or 0) <= target]
            f = (max(under, key=lambda x: x.get("height", 0)) if under
                 else min(cands, key=lambda x: x.get("height", 0)))
            try:
                data = requests.get(f["link"], timeout=90).content
                out_dir = os.path.join(config.OUTPUT_DIR, "clips")
                os.makedirs(out_dir, exist_ok=True)
                path = os.path.join(out_dir, f"clip_{idx:02d}.mp4")
                with open(path, "wb") as fh:
                    fh.write(data)
                print(f"[media]   pexels {f.get('width')}x{f.get('height')} "
                      f"({len(data)//1024}KB) id={v.get('id')}")
                return path, str(v.get("id"))
            except Exception:
                continue
    except Exception as e:
        print(f"[media] Pexels video failed for {query!r}: {e}")
    return None, None


def _pixabay_video(query: str, idx: int, exclude=None):
    """Pixabay free video (CC0, no attribution). PIXABAY_API_KEY chahiye."""
    key = os.getenv("PIXABAY_API_KEY")
    if not key:
        return None, None
    try:
        r = requests.get("https://pixabay.com/api/videos/",
                         params={"key": key, "q": query, "per_page": 8,
                                 "safesearch": "true"}, timeout=30)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        random.shuffle(hits)
        exclude = exclude or set()
        hits = [h for h in hits if str(h.get("id")) not in exclude] + \
               [h for h in hits if str(h.get("id")) in exclude]
        for h in hits:
            vf = h.get("videos", {})
            # 'small' pehle -> chhoti file (81MB 'medium' waste tha), fast render
            pick = next((vf[k] for k in ("small", "medium", "tiny", "large")
                         if vf.get(k) and vf[k].get("url")), None)
            if not pick:
                continue
            try:
                data = requests.get(pick["url"], timeout=90).content
                out_dir = os.path.join(config.OUTPUT_DIR, "clips")
                os.makedirs(out_dir, exist_ok=True)
                path = os.path.join(out_dir, f"clip_{idx:02d}.mp4")
                with open(path, "wb") as fh:
                    fh.write(data)
                print(f"[media]   pixabay clip ({len(data)//1024}KB) id={h.get('id')}")
                return path, str(h.get("id"))
            except Exception:
                continue
    except Exception as e:
        print(f"[media] Pixabay video failed for {query!r}: {e}")
    return None, None


def _coverr_video(query: str, idx: int, exclude=None):
    """Coverr free video (no attribution). COVERR_API_KEY chahiye."""
    key = os.getenv("COVERR_API_KEY")
    if not key:
        return None, None
    try:
        r = requests.get("https://api.coverr.co/videos",
                         params={"query": query, "page_size": 8, "urls": "true"},
                         headers={"Authorization": f"Bearer {key}"}, timeout=30)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        random.shuffle(hits)
        exclude = exclude or set()
        hits = [h for h in hits if str(h.get("id")) not in exclude] + \
               [h for h in hits if str(h.get("id")) in exclude]
        for h in hits:
            urls = h.get("urls", {})
            link = urls.get("mp4_download") or urls.get("mp4")
            if not link:
                continue
            try:
                data = requests.get(link, timeout=90).content
                out_dir = os.path.join(config.OUTPUT_DIR, "clips")
                os.makedirs(out_dir, exist_ok=True)
                path = os.path.join(out_dir, f"clip_{idx:02d}.mp4")
                with open(path, "wb") as fh:
                    fh.write(data)
                print(f"[media]   coverr clip ({len(data)//1024}KB) id={h.get('id')}")
                return path, str(h.get("id"))
            except Exception:
                continue
    except Exception as e:
        print(f"[media] Coverr video failed for {query!r}: {e}")
    return None, None


def _get_clip(query: str, idx: int, exclude=None):
    """MULTI-SOURCE real clip: Pexels -> Pixabay -> Coverr (variety + repeat kam)."""
    for fn in (_pexels_video, _pixabay_video, _coverr_video):
        path, vid = fn(query, idx, exclude=exclude)
        if path:
            return path, vid
    return None, None


# ── Public API ───────────────────────────────────────────────────────────────────
def fetch_media(segments: list[dict], user_images: list[str] = None,
                user_videos: list[str] = None, mode: str = "") -> list[dict]:
    """
    Har segment ke liye media descriptor: {"type": "image"|"video", "path": ".."}

    Priority: user video/image upload > LIBRARY (assets/library random clip) >
    Pexels video > real photo (named) > AI image. Sab RANDOM (repeat nahi hota).
    """
    user_images = user_images or []
    user_videos = user_videos or []
    lib = _library_files()
    random.shuffle(lib)     # har video me alag order = variety
    lib_i = 0
    out = []

    # cross-video dedup — jo pehle use ho chuke wo avoid (har video me alag visuals)
    try:
        import history
        used_real = history.used("real_photos")
        used_pex = history.used("pexels_ids")
    except Exception:
        history = None
        used_real, used_pex = set(), set()

    main_subject = _main_subject(segments)   # stat cards ke background ke liye
    _news_date = getattr(config, "NEWS_DATE", "") or None
    # Player-video (quiz NAHI) me atmospheric 'ai' segments par bhi MAIN player ki asli
    # photo dikhao (generic clip nahi). Quiz me reveal tak mystery rakhni hai -> skip.
    _player_mode = bool(main_subject) and mode.lower() != "quiz"
    if _player_mode:
        print(f"[media] player-mode: '{main_subject}' ki asli photo har segment pe")

    for i, seg in enumerate(segments):
        query = (seg.get("image_query") or "").strip() or config.TOPIC
        itype = (seg.get("image_type") or seg.get("image_source") or "ai").lower()
        ai_prompt = (f"{query}, cinematic SOCCER (association football) photography, "
                     f"soccer players in kit on green grass pitch, stadium, round "
                     f"soccer ball, dramatic lighting, high detail, vertical, "
                     f"NOT american football, no helmet")

        # 1) User uploaded VIDEO for this segment
        if i < len(user_videos) and user_videos[i]:
            print(f"[media] Segment {i+1}: USER video")
            out.append({"type": "video", "path": user_videos[i]})
            continue

        # 2) User uploaded IMAGE
        if i < len(user_images) and user_images[i]:
            try:
                img = _grade(_cover_crop(Image.open(user_images[i]),
                                         config.WIDTH, config.HEIGHT))
                out.append({"type": "image", "path": _save(img, i)})
                print(f"[media] Segment {i+1}: USER image")
                continue
            except Exception as e:
                print(f"[media] Segment {i+1}: user image failed ({e})")

        # 3) LIBRARY — atmospheric segments ke liye tumhare collect kiye clips (random)
        if lib and itype != "real":
            f = lib[lib_i % len(lib)]
            lib_i += 1
            if f.lower().endswith(_VID_EXT):
                print(f"[media] Segment {i+1}: LIBRARY clip -> {os.path.basename(f)}")
                out.append({"type": "video", "path": f})
                continue
            try:
                img = _grade(_cover_crop(Image.open(f), config.WIDTH, config.HEIGHT))
                out.append({"type": "image", "path": _save(img, i)})
                print(f"[media] Segment {i+1}: LIBRARY image -> {os.path.basename(f)}")
                continue
            except Exception:
                pass

        print(f"[media] Segment {i+1}: [{itype}] query={query!r}")

        # 3b) STAT segment -> main player (Ronaldo) ki real photo background
        #     (bade number ke peeche relevant + readable, random stadium nahi)
        if (getattr(config, "STATS_OVERLAY", False) and main_subject
                and getattr(config, "USE_REAL_PHOTO_LAYER", False)
                and _STAT_RE.search(seg.get("subtitle_english", ""))):
            try:
                from realphoto import real_photo
                rimg, rcredit, rfn = real_photo(main_subject, sentence=None,
                                                exclude=used_real, date=_news_date)
                if rimg is not None:
                    used_real.add(str(rfn))
                    if history:
                        history.mark("real_photos", rfn)
                    rimg = _grade(_cover_crop(rimg, config.WIDTH, config.HEIGHT))
                    out.append({"type": "image", "path": _save(rimg, i),
                                "credit": rcredit})
                    print(f"[media]   STAT bg -> {main_subject} real photo")
                    continue
            except Exception as e:
                print(f"[media]   stat-bg fail ({e})")

        # 4) NAMED player/team (itype 'real') -> ASLI photo PEHLE. Generic stock clip
        #    named player nahi dikhata (random log dikhte => fake lagta). User: REAL
        #    dikhao. Toh Ronaldo/Messi ke liye unki asli photo (Wikidata/Commons, legal)
        #    priority; photo na mile TABHI clip/AI (niche). Photo Ken-Burns se animate hoti.
        credit = None
        img = None
        # 'real' segment = us line ka named player. Player-mode me 'ai'/atmospheric segment
        # par bhi MAIN player ki asli photo (query abstract hota, isliye main_subject use).
        real_name = query if itype == "real" else (
            main_subject if _player_mode else None)
        if real_name and getattr(config, "USE_REAL_PHOTO_LAYER", False):
            try:
                from realphoto import real_photo
                sent = seg.get("subtitle_english") if getattr(
                    config, "REAL_PHOTO_CLIP", True) else None
                img, credit, fname = real_photo(
                    real_name, sentence=sent, exclude=used_real,
                    date=getattr(config, "NEWS_DATE", "") or None)
                if img is not None:
                    used_real.add(str(fname))              # is video me dobara na aaye
                    if history:
                        history.mark("real_photos", fname)  # future videos me na aaye
                    img = _grade(_cover_crop(img, config.WIDTH, config.HEIGHT))
                    out.append({"type": "image", "path": _save(img, i),
                                "credit": credit})
                    print(f"[media]   REAL photo of '{real_name}' (actual player) credit={credit}")
                    continue
            except Exception as e:
                print(f"[media]   real-photo fail ({e}) -> clip/AI fallback")
            img = None

        # 5) VIDEO CLIP — atmospheric/generic segments (ya real jiska photo NA mila).
        _prefer_vid = getattr(config, "PREFER_VIDEO_CLIPS", False)
        if config.VIDEO_SOURCE == "pexels" and (_prefer_vid or itype != "real"):
            if itype == "real":
                q = _BROLL[i % len(_BROLL)]               # named player -> football b-roll
            else:
                q = query if query and query.lower() not in (
                    "football stadium", "football stadium action") \
                    else _BROLL[i % len(_BROLL)]
            clip, vid = _get_clip(q, i, exclude=used_pex)
            if not clip:
                clip, vid = _get_clip(_BROLL[(i + 2) % len(_BROLL)], i,
                                      exclude=used_pex)
            if not clip:
                clip, vid = _get_clip(_BROLL[(i + 4) % len(_BROLL)], i,
                                      exclude=used_pex)
            if clip:
                if vid:
                    used_pex.add(vid)
                    if history:
                        history.mark("pexels_ids", vid)
                print(f"[media]   REAL video clip (multi-source)")
                out.append({"type": "video", "path": clip})
                continue
            else:
                print(f"[media]   no clip -> image fallback")

        # 6) Image route (sab RANDOM seed/result -> repeat nahi)
        img = None
        credit = None

        if img is not None:
            pass
        elif getattr(config, "SAFE_MODE", True):
            if itype == "real":
                img = _pexels(query) or _pollinations(ai_prompt)
            else:
                img = _pollinations(ai_prompt) or _pexels(query)
        elif itype == "real":
            img = (_openverse(f"{query} football")
                   or _wikimedia(f"{query} footballer") or _wikimedia(query)
                   or _pexels(query) or _pollinations(ai_prompt))
        else:
            if config.PREFER_REAL_IMAGES:
                img = _openverse(random.choice(_BROLL)) or _openverse(random.choice(_BROLL))
            if img is None:
                img = _pollinations(ai_prompt) or _wikimedia(query)

        if img is None:
            img = Image.new("RGB", (config.WIDTH, config.HEIGHT), (15, 30, 60))

        img = _grade(_cover_crop(img, config.WIDTH, config.HEIGHT))
        out.append({"type": "image", "path": _save(img, i), "credit": credit})
        print(f"[media]   saved image")

    return out


# Backward-compat: pehle fetch_images use hota tha (sirf image paths)
def fetch_images(segments: list[dict], user_images: list[str] = None) -> list[str]:
    return [m["path"] for m in fetch_media(segments, user_images)]


if __name__ == "__main__":
    demo = [{"image_type": "ai", "image_query": "football stadium fireworks"}]
    print(fetch_media(demo))
