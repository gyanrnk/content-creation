"""
seo.py — FREE SEO layer: log YouTube/Google pe ACTUALLY kya search karte hain, wahi topic banao.

Koi API key nahi. Google/YouTube autocomplete (suggestqueries) use karta hai — ye woh real
queries deta hai jo log type karte hain, aur order khud ek demand-ranking hai (upar = zyada searched).

Use:
    env\\Scripts\\python.exe seo.py                 # aaj ke SEO topics
    env\\Scripts\\python.exe seo.py "ronaldo"       # ek seed ke suggestions
    from seo import seo_topics, suggest, rank
"""

import sys
import json
import re
import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_H = {"User-Agent": "Mozilla/5.0 (FootyShorts/1.0)"}
_SUGGEST = "https://suggestqueries.google.com/complete/search"

# Football-relevance filter (junk queries hatane ke liye)
_FOOTBALL = ("football", "soccer", "world cup", "fifa", "uefa", "champions", "goal",
             "messi", "ronaldo", "mbappe", "neymar", "haaland", "pele", "maradona",
             "ballon", "penalty", "hat trick", "hattrick", "striker", "vs", "record",
             "brazil", "argentina", "france", "portugal", "spain", "real madrid",
             "barcelona", "premier league", "la liga", "transfer", "wc 2026")

# Wrong-intent queries — log yahan actual FOOTAGE/LIVE dhoondh rahe (copyright + hamare
# narrated-short format ke liye bekaar). In words wali queries skip karo.
_SKIP = ("live", "highlights", "full match", "stream", "song", "compilation",
         "reaction", "download", "watch", "online", "meme", "robot", "channel",
         "malayalam", "tamil", "telugu", "hindi commentary", "free", "apk", "game",
         "pes", "fifa mobile", "efootball", "fc 25", "fc 26", "ea sports")

# Default seeds — inpe autocomplete maar ke real demand nikalte hain
DEFAULT_SEEDS = [
    "fifa world cup 2026", "world cup 2026", "ronaldo", "messi", "mbappe",
    "world cup 2026 ", "ronaldo vs messi", "football", "haaland",
]

# Modifiers jo autocomplete ko "agla word" dene par majboor karte hain (behtar demand mining)
_MODS = ["", " ", " 2026", " vs", " goals", " record", " world cup"]


def _suggest_raw(q: str, youtube: bool = True) -> list:
    """Raw autocomplete list ek query ke liye (order = popularity proxy)."""
    params = {"client": "firefox", "q": q, "hl": "en"}
    if youtube:
        params["ds"] = "yt"          # YouTube suggestions
    try:
        r = requests.get(_SUGGEST, params=params, headers=_H, timeout=10)
        r.encoding = "utf-8"
        data = json.loads(r.text)    # [query, [suggestions...], ...]
        return data[1] if len(data) > 1 and isinstance(data[1], list) else []
    except Exception:
        return []


def suggest(seed: str, youtube: bool = True) -> list[str]:
    """Ek seed ke around real search queries (modifiers ke saath deep mine)."""
    seen, out = set(), []
    for m in _MODS:
        for s in _suggest_raw((seed + m).strip(), youtube):
            s = (s or "").strip().lower()
            if s and s not in seen and len(s) > 3:
                seen.add(s)
                out.append(s)
    return out


def _relevant(q: str) -> bool:
    return any(k in q for k in _FOOTBALL) and not any(k in q for k in _SKIP)


def _titlecase(q: str) -> str:
    q = re.sub(r"\s+", " ", q).strip()
    return q[:1].upper() + q[1:] if q else q


def seo_topics(n: int = 10, seeds: list[str] = None) -> list[str]:
    """Real search-demand se ranked football topics (SEO-optimized)."""
    seeds = seeds or DEFAULT_SEEDS
    score = {}           # query -> demand score
    for seed in seeds:
        sugg = suggest(seed, youtube=True)
        for pos, q in enumerate(sugg):
            if not _relevant(q):
                continue
            # upar aana + baar-baar aana = zyada demand
            score[q] = score.get(q, 0) + (len(sugg) - pos)
    ranked = sorted(score.items(), key=lambda kv: kv[1], reverse=True)
    out, seen = [], set()
    for q, _ in ranked:
        key = q.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(_titlecase(q))
        if len(out) >= n:
            break
    return out


def _keywords(topic: str) -> str:
    """Topic se search-friendly seed (pehle 4 significant words)."""
    words = re.findall(r"[a-zA-Z0-9]+", topic.lower())
    stop = {"the", "a", "an", "of", "to", "and", "vs", "in", "on", "ka", "ke", "ki"}
    kw = [w for w in words if w not in stop][:4]
    return " ".join(kw)


def rank(topics: list[str]) -> list[str]:
    """Diye gaye topics ko real search demand ke hisaab se sort karo (best pehle)."""
    scored = []
    for t in topics:
        seed = _keywords(t)
        sugg = suggest(seed, youtube=True) if seed else []
        tset = set(re.findall(r"[a-zA-Z0-9]+", t.lower()))
        # kitne real suggestions is topic ke words se overlap karte hain = demand
        overlap = sum(1 for s in sugg if tset & set(re.findall(r"[a-zA-Z0-9]+", s)))
        scored.append((overlap, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        seed = sys.argv[1]
        print(f"\n🔎 '{seed}' ke real YouTube search queries:\n")
        for i, q in enumerate(suggest(seed), 1):
            print(f"  {i}. {q}")
    else:
        print("\n🎯 SEO topics (real search demand se ranked):\n")
        for i, t in enumerate(seo_topics(12), 1):
            print(f"  {i}. {t}")
    print()
