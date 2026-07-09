"""
trends.py — Aaj ke trending football topics laata hai (FREE, no key).

Google News RSS use karta hai. Timely content = algorithm boost = zyada reach.

Use:
    env\\Scripts\\python.exe trends.py            # default football trends
    env\\Scripts\\python.exe trends.py "Messi"    # kisi topic ke trends
"""

import sys
import re
import html
import urllib.parse
import xml.etree.ElementTree as ET
import requests

_HEADERS = {"User-Agent": "Mozilla/5.0 (FootyShorts/1.0)"}


def get_trending(query: str = None, n: int = 12) -> list[str]:
    """Current football headlines -> short topic strings (clean, deduped)."""
    q = query or "football OR soccer world cup"
    url = ("https://news.google.com/rss/search?q="
           + urllib.parse.quote(q)
           + "&hl=en-IN&gl=IN&ceid=IN:en")
    try:
        r = requests.get(url, headers=_HEADERS, timeout=20)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        out = []
        for it in root.findall(".//item"):
            t = html.unescape(it.findtext("title") or "").strip()
            # " - Publisher" suffix hatao
            t = re.sub(r"\s+-\s+[^-]+$", "", t).strip()
            if t and t not in out and len(t) > 15:
                out.append(t)
            if len(out) >= n:
                break
        return out
    except Exception as e:
        print(f"[trends] failed: {e}")
        return []


def wiki_facts(name: str) -> str:
    """Player/team ka Wikipedia intro (REAL career facts: clubs, trophies, records) —
    script grounding ke liye taaki LLM invent na kare. Fail par khaali."""
    import urllib.parse
    if not name or not name.strip():
        return ""
    try:
        r = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + urllib.parse.quote(name.strip().replace(" ", "_")),
            headers=_HEADERS, timeout=15)
        if r.status_code == 200:
            ex = (r.json().get("extract") or "").strip()
            return ex[:800]
    except Exception:
        pass
    return ""


def current_context(topic: str = None, n: int = 8) -> str:
    """Aaj ki REAL football headlines — script LLM ko grounding dene ke liye.

    Ye 'ground truth' hai: eliminated teams, latest results etc. LLM inke against
    kuch nahi bolega (stale prediction se bachne ke liye).
    """
    heads = get_trending(topic or "FIFA World Cup 2026 result", n=n)
    if not heads:
        # topic-specific na mile to general WC news try karo
        heads = get_trending("FIFA World Cup 2026", n=n)
    return "\n".join(f"- {h}" for h in heads) if heads else ""


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"\n🔥 Trending football topics{' for ' + repr(q) if q else ''}:\n")
    for i, t in enumerate(get_trending(q), 1):
        print(f"  {i}. {t}")
    print("\nEk topic uthao aur config.TOPIC me daalo (ya app me use karo).\n")
