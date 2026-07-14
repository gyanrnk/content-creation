"""
realphoto.py — Real, specific, LEGAL player/team/stadium photos.

Strategy (free + monetization-safe):
  1. Wikidata P18   -> entity ka canonical real photo (best precision)
  2. Wikipedia lead -> article ki lead image
  3. Commons search -> aur candidates (variety)
  4. CLIP rerank    -> sentence ke liye SABSE relevant photo pick (optional, free)

Sab CC/PD licensed (attribution honor karna — TODO: attribution card).
"""

import io
import re
import urllib.parse
import requests
from PIL import Image

_H = {"User-Agent": "FootyShorts/1.0 (educational content generator)"}


def _get(url, **kw):
    return requests.get(url, headers=_H, timeout=25, **kw)


# Ambiguous football names -> canonical full name (warna Wikidata galat entity uthata:
# "Ronaldo" -> Brazil ka Ronaldo Nazario aa jaata tha jabki Cristiano chahiye tha).
_ALIAS = {
    "ronaldo": "Cristiano Ronaldo",
    "cr7": "Cristiano Ronaldo",
    "cristiano": "Cristiano Ronaldo",
    "messi": "Lionel Messi",
    "leo messi": "Lionel Messi",
    "leo": "Lionel Messi",
    "mbappe": "Kylian Mbappe",
    "neymar": "Neymar",
    "haaland": "Erling Haaland",
    "pele": "Pele",
    "maradona": "Diego Maradona",
    # Brazil ka Ronaldo alag se maangna ho to explicit:
    "ronaldo nazario": "Ronaldo (Brazilian footballer)",
    "ronaldo nazário": "Ronaldo (Brazilian footballer)",
    "brazilian ronaldo": "Ronaldo (Brazilian footballer)",
    "r9": "Ronaldo (Brazilian footballer)",
    "ronaldo brazil": "Ronaldo (Brazilian footballer)",
}


def _canonical(name: str) -> str:
    """Ambiguous naam ko full canonical banao (galat image se bachao)."""
    key = re.sub(r"\s+", " ", (name or "").strip().lower())
    if key in _ALIAS:
        return _ALIAS[key]
    # "ronaldo" akela/andar ho par cristiano/nazario/brazil na ho -> Cristiano maano
    if "ronaldo" in key and not any(w in key for w in
                                    ("cristiano", "nazario", "nazário", "brazil", "r9")):
        return re.sub(r"\bronaldo\b", "Cristiano Ronaldo", name, flags=re.I)
    return name


def _wikidata_p18(name: str):
    """Entity search -> Q-id -> P18 image filename -> Commons FilePath URL."""
    try:
        r = _get("https://www.wikidata.org/w/api.php",
                 params={"action": "wbsearchentities", "search": name,
                         "language": "en", "format": "json", "type": "item",
                         "limit": 1})
        hits = r.json().get("search", [])
        if not hits:
            return None
        qid = hits[0]["id"]
        r2 = _get("https://www.wikidata.org/w/api.php",
                  params={"action": "wbgetclaims", "entity": qid,
                          "property": "P18", "format": "json"})
        claims = r2.json().get("claims", {}).get("P18", [])
        if not claims:
            return None
        fn = claims[0]["mainsnak"]["datavalue"]["value"]
        return ("https://commons.wikimedia.org/wiki/Special:FilePath/"
                + requests.utils.quote(fn) + "?width=1200")
    except Exception:
        return None


def _wiki_lead(title: str):
    try:
        r = _get("https://en.wikipedia.org/api/rest_v1/page/summary/"
                 + requests.utils.quote(title))
        if r.status_code != 200:
            return None
        return r.json().get("originalimage", {}).get("source")
    except Exception:
        return None


def _commons_search(query: str, n: int = 6):
    """Returns list of (url, year) — year = photo kab li gayi (metadata se), ya None."""
    try:
        r = _get("https://commons.wikimedia.org/w/api.php",
                 params={"action": "query", "format": "json",
                         "generator": "search", "gsrsearch": query,
                         "gsrnamespace": 6, "gsrlimit": n,
                         "prop": "imageinfo", "iiprop": "url|mime|extmetadata",
                         "iiurlwidth": 1200})
        pages = r.json().get("query", {}).get("pages", {})
        out = []
        for p in pages.values():
            ii = p.get("imageinfo", [{}])[0]
            u = ii.get("thumburl") or ii.get("url")
            mime = ii.get("mime", "")
            if not (u and mime.startswith("image") and "svg" not in mime):
                continue
            ext = ii.get("extmetadata", {})
            raw = (ext.get("DateTimeOriginal", {}).get("value", "")
                   or ext.get("DateTime", {}).get("value", ""))
            ym = re.search(r"(19|20)\d\d", raw)
            out.append((u, int(ym.group(0)) if ym else None))
        return out
    except Exception:
        return []


def _openverse_photos(query: str, n: int = 6):
    """Openverse (CC image aggregator: Flickr + Commons + museums, NO API key) se
    COMMERCIAL-safe + modification-allowed photos. Flickr ke press/fan shots aksar
    Wikimedia se ZYADA RECENT hote hain. Returns list of (url, year, credit)."""
    try:
        r = _get("https://api.openverse.org/v1/images/",
                 params={"q": query, "page_size": n,
                         "license_type": "commercial,modification",
                         "mature": "false"})
        out = []
        for it in r.json().get("results", []):
            u = it.get("url")
            if not u:
                continue
            creator = (it.get("creator") or "").strip()
            lic = (it.get("license") or "").upper()
            ver = (it.get("license_version") or "").strip()
            tag = f"CC {lic} {ver}".strip()
            credit = f"{creator} ({tag})" if creator and lic else (tag or None)
            out.append((u, None, credit))
        return out
    except Exception:
        return []


def _download(url: str):
    try:
        r = _get(url)
        if r.status_code == 200 and len(r.content) > 3000:
            img = Image.open(io.BytesIO(r.content))
            if img.width >= 500 and img.height >= 500:
                return img.convert("RGB")
    except Exception:
        pass
    return None


# ── CLIP rerank (lazy) ──────────────────────────────────────────────────────────
_clip = None


def _clip_model():
    global _clip
    if _clip is None:
        from sentence_transformers import SentenceTransformer
        _clip = SentenceTransformer("clip-ViT-B-32")
    return _clip


def _clip_best_idx(sentence: str, images: list) -> int:
    """Sentence ke liye sabse relevant image ka index (cosine similarity)."""
    try:
        from sentence_transformers import util
        m = _clip_model()
        tvec = m.encode([sentence])
        ivec = m.encode(images)          # PIL images directly
        sims = util.cos_sim(tvec, ivec).numpy()[0]
        return int(sims.argmax())
    except Exception as e:
        print(f"[realphoto] CLIP skip ({e}) -> using first")
        return 0


# ── Attribution (CC-BY -> credit line) ──────────────────────────────────────────
def _filename_from_url(url: str):
    url = urllib.parse.unquote(url)
    if "Special:FilePath/" in url:
        return url.split("Special:FilePath/")[1].split("?")[0]
    m = re.search(r"/commons/(?:thumb/)?[0-9a-f]/[0-9a-f]{2}/([^/]+)", url)
    return m.group(1) if m else None


def _credit_for(url: str):
    """Commons imageinfo se author + license -> credit string."""
    try:
        fn = _filename_from_url(url)
        if not fn:
            return None
        r = _get("https://commons.wikimedia.org/w/api.php",
                 params={"action": "query", "format": "json",
                         "titles": "File:" + fn, "prop": "imageinfo",
                         "iiprop": "extmetadata"})
        pages = r.json().get("query", {}).get("pages", {})
        for p in pages.values():
            ext = p.get("imageinfo", [{}])[0].get("extmetadata", {})
            artist = re.sub("<[^>]+>", "",
                            ext.get("Artist", {}).get("value", "")).strip()
            lic = ext.get("LicenseShortName", {}).get("value", "").strip()
            if artist and lic:
                return f"{artist} ({lic})"
            if lic:
                return lic
            if artist:
                return artist
    except Exception:
        pass
    return None


def real_photo(query: str, sentence: str = None, n: int = 10, exclude=None,
               date: str = None):
    """
    query    = entity name ("Lionel Messi", "Brazil national football team")
    sentence = full English subtitle (CLIP isse best match pick karega)
    exclude  = filenames pehle use ho chuke (cross-video variety ke liye skip)
    date     = "2012" ya "2012-06-15" -> us era/date ke aas-paas ki photo prefer
    Returns (PIL.Image RGB, credit_string, filename). Fail = (None, None, None).
    """
    exclude = exclude or set()
    query = _canonical(query)          # ambiguity fix (Ronaldo -> Cristiano Ronaldo)
    target_year = None
    if date:
        m = re.search(r"(19|20)\d\d", str(date))
        if m:
            target_year = int(m.group(0))

    cands = []   # dicts {url, fn, year}

    def _add(u, year=None, credit=None):
        if not u:
            return
        cands.append({"url": u, "fn": _filename_from_url(u),
                      "year": year, "credit": credit})

    _add(_wikidata_p18(query))
    _add(_wiki_lead(query.replace(" ", "_")))
    # date ho to year search me daalo (event/era relevance)
    q = f"{query} {target_year}" if target_year else query
    for u, yr in _commons_search(f"{q} footballer", n):
        _add(u, yr)
    for u, yr in _commons_search(q, n):
        _add(u, yr)
    # Openverse (Flickr etc.) — zyada candidates + aksar RECENT match photos, key-free.
    # Sirf naam (extra words se result 0 ho jaate); unique naam = football hi milta.
    for u, yr, cr in _openverse_photos(query, n):
        _add(u, yr, cr)

    # dedupe
    seen, uniq = set(), []
    for c in cands:
        key = c["fn"] or c["url"]
        if key not in seen:
            seen.add(key)
            uniq.append(c)

    # non-photo junk hatao (graffiti, statue, logo, cartoon, etc.)
    # English + common non-English junk (statue/art) — "Escultura de Ronaldo" jaise
    # statue filenames English regex se bach jaate the.
    _JUNK = re.compile(r"graffiti|mural|statue|sculpture|\blogo\b|coin|banknote|"
                       r"stamp|drawing|cartoon|artwork|wax|figurine|painting|"
                       r"mosaic|street.?art|caricature|emblem|badge|"
                       r"escultura|estatua|est[aá]tua|skulptur|standbeeld|statula|"
                       r"pintura|dibujo|peinture|zeichnung|busto|\bbust\b|monument|"
                       r"denkmal|estatura|maquette|figuur", re.I)
    filt = [c for c in uniq if not _JUNK.search(c["fn"] or "")]
    if filt:
        uniq = filt

    # fresh (unused) pehle; date ho to date-proximity se sort (unknown year = door)
    fresh = [c for c in uniq if (c["fn"] or c["url"]) not in exclude]
    stale = [c for c in uniq if (c["fn"] or c["url"]) in exclude]
    if target_year:
        fresh.sort(key=lambda c: abs((c["year"] or target_year + 60) - target_year))
    ordered = fresh + stale

    pairs = []   # (url, fn, image, credit)
    for c in ordered:
        img = _download(c["url"])
        if img:
            pairs.append((c["url"], c["fn"], img, c.get("credit")))
        if len(pairs) >= n:
            break
    if not pairs:
        return None, None, None

    fresh_pairs = [p for p in pairs if (p[1] or p[0]) not in exclude] or pairs
    # date ho to closest-era candidates ko priority (top 4 me se CLIP pick)
    pool = fresh_pairs[:4] if target_year else fresh_pairs
    if sentence and len(pool) > 1:
        idx = _clip_best_idx(sentence, [im for _, _, im, _ in pool])
    else:
        idx = 0
    url, fn, img, cr = pool[idx]
    print(f"[realphoto] {query!r} date={target_year}: {len(pairs)} cands")
    return img, (cr or _credit_for(url)), (fn or url)


if __name__ == "__main__":
    img, credit, fn = real_photo("Lionel Messi", "Messi lifting the World Cup trophy")
    if img:
        img.save("output/realphoto_test.jpg")
        print("saved:", img.size, "| credit:", credit, "| file:", fn)
    else:
        print("no photo found")
